import pickle
from pathlib import Path
from typing import Set, Union

from tkinter import Tk, messagebox

import attr
from Crypto import Random
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from Crypto.Signature import pkcs1_15
import base64


class BugReporter:

    _PUBLIC_KEY = "public key"
    _SIGNATURE = "signature"
    _BUGS_FOUND = "bugs found"

    @attr.s(frozen=True)
    class Bug:
        title = attr.ib()
        description = attr.ib()

    def __init__(self, path: Union[Path, str]):
        if not isinstance(path, Path):
            path = Path(path)
        self.private_key = self.__generate_private_key()
        self.public_key = self.private_key.publickey()
        self.bugs_found = self.__verify_and_load(path)
        self.output_path = path

    @staticmethod
    def __verify_and_load(path: Path) -> Set[Bug]:
        try:
            if not all([path.exists(),
                        path.joinpath(BugReporter._PUBLIC_KEY).exists(),
                        path.joinpath(BugReporter._SIGNATURE).exists(),
                        path.joinpath(BugReporter._BUGS_FOUND).exists()]):
                return set()

            with path.joinpath(BugReporter._PUBLIC_KEY).open("rb") as pubkey:
                public_key = RSA.import_key(pubkey.read())

            with path.joinpath(BugReporter._SIGNATURE).open("rb") as sig:
                signature = sig.read()

            with path.joinpath(BugReporter._BUGS_FOUND).open("rb") as bf:
                bugs_found = bf.read()

            # Verify that the signature matches bugs found
            h = SHA256.new(bugs_found)
            try:
                pkcs1_15.new(public_key).verify(h, signature)
            except ValueError:
                return set()

            return pickle.loads(bugs_found)
        except Exception:
            return set()

    @staticmethod
    def __generate_private_key():
        length = 2 ** 10
        return RSA.generate(length, Random.new().read)

    def report_bug(self, bug_title: str, bug_description: str):
        """
        Report a bug.
        :param bug_title: The bug's name.
        :param bug_description: A description of the bug
        """
        bug = BugReporter.Bug(bug_title, bug_description)
        if bug not in self.bugs_found:
            self._show_messagebox(bug)
            self.bugs_found.add(bug)
            self._save_state()

    def _show_messagebox(self, bug):
        Tk().wm_withdraw()
        messagebox.showinfo(bug.title, bug.description)

    def _save_state(self):
        message = pickle.dumps(self.bugs_found)
        h = SHA256.new(message)
        signature = pkcs1_15.new(self.private_key).sign(h)

        if not self.output_path.exists():
            self.output_path.mkdir(parents=True)

        with self.output_path.joinpath(BugReporter._PUBLIC_KEY).open("wb") as pubkey:
            pubkey.write(self.public_key.export_key())

        with self.output_path.joinpath(BugReporter._SIGNATURE).open("wb") as sig:
            sig.write(signature)

        with self.output_path.joinpath(BugReporter._BUGS_FOUND).open("wb") as bf:
            bf.write(message)


bug_reporter = BugReporter("./bug reports")
