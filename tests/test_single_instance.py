from __future__ import annotations

import os
import subprocess
import sys
import textwrap
import unittest
from pathlib import Path

from aero_recorder.single_instance import (
    MUTEX_NAME,
    SHOW_WINDOW_MESSAGE_NAME,
    SingleInstance,
)


class NamingTests(unittest.TestCase):
    def test_mutex_is_scoped_to_the_local_session(self) -> None:
        # "Local\" keeps the mutex inside the current session. A "Global\" name
        # would let a process in another session block this one from starting,
        # and would let an unprivileged process squat the name.
        self.assertTrue(MUTEX_NAME.startswith("Local\\"))

    def test_mutex_name_is_specific_to_aerorecorder(self) -> None:
        self.assertIn("AeroRecorder", MUTEX_NAME)

    def test_names_contain_a_stable_unique_suffix(self) -> None:
        # A generic name like "AeroRecorder" could collide with another program.
        self.assertRegex(MUTEX_NAME, r"[0-9a-fA-F]{8}")
        self.assertRegex(SHOW_WINDOW_MESSAGE_NAME, r"[0-9a-fA-F]{8}")

    def test_names_are_not_equal(self) -> None:
        self.assertNotEqual(MUTEX_NAME, SHOW_WINDOW_MESSAGE_NAME)


class AcquireTests(unittest.TestCase):
    def test_first_acquire_in_this_process_succeeds(self) -> None:
        guard = SingleInstance(name="Local\\AeroRecorderTest-first")
        try:
            self.assertTrue(guard.acquire())
        finally:
            guard.release()

    def test_second_guard_on_the_same_name_is_refused(self) -> None:
        name = "Local\\AeroRecorderTest-duplicate"
        first = SingleInstance(name=name)
        second = SingleInstance(name=name)
        try:
            self.assertTrue(first.acquire())
            self.assertFalse(
                second.acquire(),
                "a second guard on the same name must report the name is taken",
            )
        finally:
            second.release()
            first.release()

    def test_releasing_frees_the_name_for_reuse(self) -> None:
        name = "Local\\AeroRecorderTest-reuse"
        first = SingleInstance(name=name)
        self.assertTrue(first.acquire())
        first.release()

        second = SingleInstance(name=name)
        try:
            self.assertTrue(
                second.acquire(),
                "the name must be reusable once the first guard releases it",
            )
        finally:
            second.release()

    def test_release_is_idempotent(self) -> None:
        guard = SingleInstance(name="Local\\AeroRecorderTest-idempotent")
        guard.acquire()
        guard.release()
        guard.release()  # must not raise

    def test_guard_works_as_a_context_manager(self) -> None:
        name = "Local\\AeroRecorderTest-context"
        with SingleInstance(name=name) as acquired:
            self.assertTrue(acquired)
            self.assertFalse(SingleInstance(name=name).acquire())
        # released on exit, so the name is free again
        again = SingleInstance(name=name)
        try:
            self.assertTrue(again.acquire())
        finally:
            again.release()


@unittest.skipUnless(os.name == "nt", "the mutex guard is Windows-specific")
class CrossProcessTests(unittest.TestCase):
    """The guard only matters across processes, so prove it there."""

    def test_a_separate_process_cannot_acquire_a_held_name(self) -> None:
        name = "Local\\AeroRecorderTest-crossprocess"
        holder = SingleInstance(name=name)
        self.assertTrue(holder.acquire())
        try:
            root = Path(__file__).resolve().parent.parent
            script = textwrap.dedent(
                f"""
                import sys
                sys.path.insert(0, {str(root)!r})
                from aero_recorder.single_instance import SingleInstance
                guard = SingleInstance(name={name!r})
                print("ACQUIRED" if guard.acquire() else "REFUSED")
                """
            )
            result = subprocess.run(
                [sys.executable, "-c", script],
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(
                result.stdout.strip(),
                "REFUSED",
                f"second process should be refused; stderr={result.stderr}",
            )
        finally:
            holder.release()

    def test_a_separate_process_can_acquire_a_free_name(self) -> None:
        root = Path(__file__).resolve().parent.parent
        script = textwrap.dedent(
            f"""
            import sys
            sys.path.insert(0, {str(root)!r})
            from aero_recorder.single_instance import SingleInstance
            guard = SingleInstance(name="Local\\\\AeroRecorderTest-freename")
            print("ACQUIRED" if guard.acquire() else "REFUSED")
            """
        )
        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(
            result.stdout.strip(),
            "ACQUIRED",
            f"an unheld name should be acquirable; stderr={result.stderr}",
        )


if __name__ == "__main__":
    unittest.main()
