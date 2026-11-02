import { vi } from 'vitest';

export function deferred() {
  let resolve;
  let reject;
  const promise = new Promise((onResolve, onReject) => {
    resolve = onResolve;
    reject = onReject;
  });
  return { promise, resolve, reject };
}

// A controllable media element: promises and browser events can arrive late.
export function mockAudio(play = () => Promise.resolve()) {
  const instances = [];

  class TestAudio extends EventTarget {
    constructor(src) {
      super();
      this.src = src;
      this.currentTime = 0;
      this.error = null;
      this.play = vi.fn(play);
      this.pause = vi.fn();
      this.load = vi.fn();
      instances.push(this);
    }

    emit(type) {
      const event = new Event(type);
      this.dispatchEvent(event);
      this[`on${type}`]?.(event);
    }
  }

  vi.spyOn(globalThis, 'Audio').mockImplementation(function (src) {
    return new TestAudio(src);
  });
  return instances;
}
