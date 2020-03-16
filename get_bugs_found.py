import argparse
from bug_reporter import BugReporter


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="The path in which the public key, signature and private key can be found.",
                        type=str)

    args = parser.parse_args()

    path = args.path
    reporter = BugReporter(path)

    bugs = list(reporter.bugs_found)
    bugs.sort(key=lambda bug: bug.title)

    for bug in bugs:
        print(f"{bug.title} - {bug.description}")


if __name__ == "__main__":
    main()
