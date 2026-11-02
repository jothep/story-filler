import { useState, useEffect, useCallback, useRef } from 'react';
import { getStoryById } from '../api/storyApi';

/** Load a story while keeping results owned by the current route and request. */
export function useStory(storyId) {
  const [state, setState] = useState({
    storyId,
    story: null,
    loading: Boolean(storyId),
    error: null,
  });
  const activeScope = useRef(null);

  const fetchStory = useCallback(async () => {
    const scope = activeScope.current;
    // A saved retry callback must not start work for an unmounted or old route.
    if (!scope || scope.storyId !== storyId) {
      return;
    }

    scope.controller?.abort();
    if (!storyId) {
      setState({ storyId, story: null, loading: false, error: null });
      return;
    }

    const controller = new AbortController();
    scope.controller = controller;
    // Cancellation saves work; identity also protects against late responses
    // from a transport that has already completed or ignores cancellation.
    const isCurrentRequest = () =>
      activeScope.current === scope &&
      scope.controller === controller &&
      !controller.signal.aborted;

    setState((current) => ({
      storyId,
      story: current.storyId === storyId ? current.story : null,
      loading: true,
      error: null,
    }));
    try {
      const data = await getStoryById(storyId, { signal: controller.signal });
      if (isCurrentRequest()) {
        setState((current) => ({ ...current, story: data }));
      }
    } catch (err) {
      if (isCurrentRequest() && err.name !== 'AbortError') {
        setState((current) => ({ ...current, error: err.message }));
      }
    } finally {
      if (isCurrentRequest()) {
        setState((current) => ({ ...current, loading: false }));
      }
    }
  }, [storyId]);

  useEffect(() => {
    const scope = { storyId, controller: null };
    activeScope.current = scope;
    void fetchStory();

    return () => {
      scope.controller?.abort();
      if (activeScope.current === scope) {
        activeScope.current = null;
      }
    };
  }, [storyId, fetchStory]);

  // Effects run after rendering. Do not expose the previous route's data or
  // error even for the first render before its replacement request starts.
  const { story, loading, error } =
    state.storyId === storyId
      ? state
      : { story: null, loading: Boolean(storyId), error: null };

  return { story, loading, error, refetch: fetchStory };
}
