"""Read-only release ordering and verification for the single Cloud Run service.

The workflow holds a deployment lock while this helper checks the serving
revision, updates the service, and verifies the result. This module never deploys.
"""

import argparse
from dataclasses import dataclass
import json
import re
import subprocess
import sys
from urllib.parse import urlsplit

COMMIT_PATTERN = re.compile(r"[0-9a-f]{40}")
DIGEST_PATTERN = re.compile(r"sha256:[0-9a-f]{64}")
SERVICE_FIELDS = (
    "metadata.generation,spec.traffic,spec.template.metadata.name,"
    "spec.template.spec.containers[0].image,status.traffic,status.url,"
    "status.observedGeneration,status.latestCreatedRevisionName,"
    "status.latestReadyRevisionName,status.conditions"
)
REVISION_FIELDS = (
    "metadata.labels.source_commit,spec.containers[0].image,status.imageDigest"
)


class ReleaseError(Exception):
    """The release cannot be identified, ordered, or verified safely."""


@dataclass(frozen=True)
class ServingRelease:
    revision: str
    commit: str
    image: str
    url: str


def command_result(arguments):
    """Capture output privately; do not print CLI diagnostics or configuration."""
    try:
        return subprocess.run(
            arguments, capture_output=True, text=True, timeout=60, check=False
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise ReleaseError(f"Could not complete the {arguments[0]} check.") from error


def describe_cloud_resource(kind, name, project, region, fields):
    result = command_result(
        [
            "gcloud",
            "run",
            kind,
            "describe",
            name,
            f"--project={project}",
            f"--region={region}",
            f"--format=json({fields})",
        ]
    )
    if result.returncode:
        raise ReleaseError(f"Could not read the Cloud Run {kind} release metadata.")
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise ReleaseError("Cloud Run returned invalid release metadata.") from error
    if not isinstance(payload, dict):
        raise ReleaseError("Cloud Run returned an unexpected metadata structure.")
    return payload


def full_image_digest(value, repository):
    prefix = repository + "@"
    if not isinstance(value, str) or not value.startswith(prefix):
        raise ReleaseError(
            "The image must use the expected repository and an immutable digest."
        )
    if not DIGEST_PATTERN.fullmatch(value.removeprefix(prefix)):
        raise ReleaseError("The image digest is missing or invalid.")
    return value


def legacy_template_commit(details, revision, repository):
    """Bind an old template's commit tag to the fully reconciled serving revision."""
    try:
        generation = details["metadata"]["generation"]
        status = details["status"]
        template = details["spec"]["template"]
        observed = status["observedGeneration"]
        if (
            type(generation) is not int
            or type(observed) is not int
            or generation < 1
            or observed != generation
            or status["latestCreatedRevisionName"] != revision
            or status["latestReadyRevisionName"] != revision
        ):
            raise ValueError
        ready = [item for item in status["conditions"] if item["type"] == "Ready"]
        if len(ready) != 1 or ready[0]["status"] != "True":
            raise ValueError
        template_name = template.get("metadata", {}).get("name")
        if template_name is not None and template_name != revision:
            raise ValueError
        tag = re.fullmatch(
            re.escape(repository) + r":([0-9a-f]{40})",
            template["spec"]["containers"][0]["image"],
        )
        if not tag:
            raise ValueError
    except (KeyError, IndexError, TypeError, ValueError, AttributeError) as error:
        raise ReleaseError(
            "The legacy service template cannot safely identify "
            "the serving revision's full source commit."
        ) from error
    return tag[1]


def serving_release(service, project, region, repository):
    details = describe_cloud_resource(
        "services", service, project, region, SERVICE_FIELDS
    )
    service_details = details
    try:
        traffic = details["status"]["traffic"]
        policy = details["spec"]["traffic"]
        url = details["status"]["url"]
        if not isinstance(traffic, list) or not isinstance(policy, list):
            raise ValueError
        if any(
            type(item.get("percent", 0)) is not int
            or not 0 <= item.get("percent", 0) <= 100
            for item in traffic + policy
        ):
            raise ValueError
        serving = [item for item in traffic if item.get("percent", 0) > 0]
        targets = [item for item in policy if item.get("percent", 0) > 0]
        if len(serving) != 1 or serving[0]["percent"] != 100:
            raise ValueError
        if (
            len(targets) != 1
            or targets[0]["percent"] != 100
            or targets[0].get("latestRevision") is not True
        ):
            raise ValueError
        revision = serving[0]["revisionName"]
        if not re.fullmatch(re.escape(service) + r"-[a-z0-9-]+", revision):
            raise ValueError
        parsed_url = urlsplit(url)
        if (
            parsed_url.scheme != "https"
            or not parsed_url.hostname
            or parsed_url.username
            or parsed_url.password
        ):
            raise ValueError
        if any(character.isspace() for character in url):
            raise ValueError
        if parsed_url.query or parsed_url.fragment or parsed_url.path not in ("", "/"):
            raise ValueError
    except (KeyError, TypeError, ValueError, AttributeError) as error:
        raise ReleaseError(
            "Require one identified serving revision "
            "and a 100% latest-revision traffic policy."
        ) from error

    details = describe_cloud_resource(
        "revisions", revision, project, region, REVISION_FIELDS
    )
    try:
        image_reference = details["spec"]["containers"][0]["image"]
        digest = details["status"]["imageDigest"]
        commit = details.get("metadata", {}).get("labels", {}).get("source_commit")
    except (KeyError, IndexError, TypeError, AttributeError) as error:
        raise ReleaseError(
            "The serving revision has incomplete image metadata."
        ) from error
    if not isinstance(image_reference, str):
        raise ReleaseError("The serving revision has no image reference.")
    legacy_tag = re.fullmatch(
        re.escape(repository) + r":([0-9a-f]{40})", image_reference
    )
    digest_reference = re.fullmatch(
        re.escape(repository) + r"@sha256:[0-9a-f]{64}", image_reference
    )
    if not legacy_tag and not digest_reference:
        raise ReleaseError(
            "The serving image reference does not belong to the expected repository."
        )
    # Some CLI/API versions return the bare digest in revision status.
    # Its repository comes from the independently validated image reference.
    if isinstance(digest, str) and DIGEST_PATTERN.fullmatch(digest):
        digest = repository + "@" + digest
    image = full_image_digest(digest, repository)
    if legacy_tag:
        # Existing releases predate source_commit labels, but used full commit tags.
        if commit is not None and commit != legacy_tag[1]:
            raise ReleaseError(
                "The serving revision's commit label and image tag disagree."
            )
        commit = legacy_tag[1]
    elif image_reference != image:
        raise ReleaseError(
            "The serving image reference does not match its resolved digest."
        )
    if commit is None and digest_reference:
        # Cloud Run resolves old revision tags to digests. Only the corresponding
        # fully ready service template can supply their original commit tag.
        commit = legacy_template_commit(service_details, revision, repository)
    if not isinstance(commit, str) or not COMMIT_PATTERN.fullmatch(commit):
        raise ReleaseError("The serving image does not identify a full source commit.")
    return ServingRelease(revision, commit, image, url)


def require_commit(commit):
    if not COMMIT_PATTERN.fullmatch(commit):
        raise ReleaseError("A full source commit is required.")
    result = command_result(["git", "cat-file", "-e", commit + "^{commit}"])
    if result.returncode:
        raise ReleaseError(
            "A release commit is absent from the checked-out repository history."
        )


def is_ancestor(older, newer):
    result = command_result(["git", "merge-base", "--is-ancestor", older, newer])
    if result.returncode not in (0, 1):
        raise ReleaseError("Could not compare release commits.")
    return result.returncode == 0


def release_decision(candidate, image, current):
    require_commit(candidate)
    require_commit(current.commit)
    # A later documentation-only commit on main must not discard this release.
    for commit in (candidate, current.commit):
        if not is_ancestor(commit, "refs/remotes/origin/main"):
            raise ReleaseError(
                "Both release commits must belong to the current main history."
            )
    if candidate == current.commit:
        if image != current.image:
            raise ReleaseError(
                "This source commit already serves a different digest; "
                "review a new release commit."
            )
        return "unchanged"
    if is_ancestor(candidate, current.commit):
        return "superseded"
    if not is_ancestor(current.commit, candidate):
        raise ReleaseError(
            "The release histories diverge; automatic deployment is refused."
        )
    return "deploy"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("plan", "verify"))
    parser.add_argument("--service", required=True)
    parser.add_argument("--project", required=True)
    parser.add_argument("--region", required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--image", required=True)
    parser.add_argument("--expected-revision")
    args = parser.parse_args(argv)
    try:
        image = full_image_digest(args.image, args.repository)
        current = serving_release(
            args.service, args.project, args.region, args.repository
        )
        if args.operation == "plan":
            decision = release_decision(args.candidate, image, current)
            print(f"deploy={'true' if decision == 'deploy' else 'false'}")
            print(f"decision={decision}")
            print(f"Release decision: {decision}.", file=sys.stderr)
        else:
            if not args.expected_revision:
                raise ReleaseError(
                    "Verification requires the revision returned by the deployment."
                )
            if (current.revision, current.commit, current.image) != (
                args.expected_revision,
                args.candidate,
                image,
            ):
                raise ReleaseError(
                    "The serving revision, commit, or digest "
                    "does not match this deployment."
                )
            print(f"service_url={current.url}")
            print(f"Verified serving revision {current.revision}.", file=sys.stderr)
    except ReleaseError as error:
        print(f"Release check failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
