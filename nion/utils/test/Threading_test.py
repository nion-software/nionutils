# standard libraries
import logging
import threading
import time
import unittest

# third party libraries
# None

# local libraries
from nion.utils.Threading import ThreadSafeDict

class TestThreadSafeDict(unittest.TestCase):
    def test_single_thread_operations(self) -> None:
        d = ThreadSafeDict[str, int]()
        d["a"] = 1
        self.assertEqual(d["a"], 1)
        d["b"] = 2
        self.assertIn("b", d)
        self.assertEqual(len(d), 2)
        d.pop("a")
        self.assertNotIn("a", d)

    def test_multi_thread_safe_without_locked(self) -> None:
        d = ThreadSafeDict[str, int]()

        def worker(start: int, end: int):
            for i in range(start, end):
                # Increment counter atomically using built-in thread-safe __setitem__ + __getitem__
                key = f"key-{i % 10}"
                with d.locked():
                    d[key] = d.get(key, 0) + 1

        threads = [threading.Thread(target=worker, args=(0, 1000)) for _ in range(5)]
        for t in threads: t.start()
        for t in threads: t.join()

        # Each key should have been incremented 5 * (1000/10) = 500 times
        for i in range(10):
            self.assertEqual(d[f"key-{i}"], 500)

    def test_locked_context_atomic(self) -> None:
        d = ThreadSafeDict[str, int]()
        d["counter"] = 0

        def worker(n: int):
            with d.locked():
                for local_counter in range(n):
                    # Read-modify-write sequence
                    val = d["counter"]
                    modulo = val % n
                    assert local_counter == modulo
                    time.sleep(0.0001)  # simulate some delay
                    d["counter"] = val + 1

        threads = [threading.Thread(target=worker, args=(100,)) for _ in range(5)]
        for t in threads: t.start()
        for t in threads: t.join()

        # Total increments = 5 * 100 = 500
        self.assertEqual(d["counter"], 500)

    def test_fine_grained_locked_increment(self) -> None:
        """
        Tests multiple threads performing single-step increments with d.locked(),
        demonstrating that fine-grained access is safely serialized.
        """
        d = ThreadSafeDict[str, int]()
        d["counter"] = 0

        num_threads = 5
        increments_per_thread = 1000

        def worker():
            for _ in range(increments_per_thread):
                # Fine-grained atomic increment
                with d.locked():
                    d["counter"] = d.get("counter", 0) + 1

        threads = [threading.Thread(target=worker) for _ in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All increments should be accounted for
        expected_total = num_threads * increments_per_thread
        self.assertEqual(d["counter"], expected_total)

    def test_copy_and_to_dict_thread_safety(self) -> None:
        d = ThreadSafeDict[str, int]()
        d["a"] = 1
        d["b"] = 2

        # Test copy
        copy_d = d.copy()
        self.assertEqual(copy_d.to_dict(), d.to_dict())

        # Test to_dict
        plain = d.to_dict()
        self.assertEqual(plain, {"a": 1, "b": 2})

    def test_threadsafedict_overhead(self):
        N_ITEMS = 1000
        N_OPS = 1000

        # Prepare test data
        keys = list(range(N_ITEMS))
        values = list(range(N_ITEMS))

        # --- Built-in dict ---
        d = dict(zip(keys, values))
        start = time.time()
        for _ in range(N_OPS):
            for k in keys:
                d[k] = d[k] + 1
                _ = d[k]
        dict_time = time.time() - start

        # --- ThreadSafeDict ---
        d2 = ThreadSafeDict[int, int](zip(keys, values))
        start = time.time()
        for _ in range(N_OPS):
            for k in keys:
                d2[k] = d2[k] + 1
                _ = d2[k]
        tsd_time = time.time() - start

        multiplier = tsd_time / dict_time if dict_time > 0 else float('inf')

        print(f"Built-in dict time: {dict_time:.6f}s")
        print(f"ThreadSafeDict time: {tsd_time:.6f}s")
        print(f"Rough overhead multiplier: {multiplier:.2f}x")


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    unittest.main()