import argparse
import os
import pathlib

import requests
from grpc_tools.protoc import main as grpc_tools_protoc_main

DEFAULT_PROTO_VERSION: str = "8.6.6"


def main():
    parser = argparse.ArgumentParser(description="Download Zeebe proto file and generate protoctol buffers.")
    parser.add_argument(
        "-pv",
        "--proto-version",
        default=[DEFAULT_PROTO_VERSION],
        nargs=1,
        type=str,
        help=f"zeebe proto version, default is {DEFAULT_PROTO_VERSION}",
        required=False,
        # NOTE: The default value is set to the latest version of Zeebe proto file.
    )
    args = parser.parse_args()

    print(f"Zeebe Proto version: {args.proto_version[0]}")
    proto_version = args.proto_version[0]
    generate_proto(proto_version)


def generate_proto(zeebe_proto_version: str):
    proto_dir = pathlib.Path("pyzeebe/proto")
    proto_file = proto_dir / "gateway.proto"
    for path in proto_dir.glob("*pb2*"):
        os.remove(path)

    proto_url = f"https://raw.githubusercontent.com/camunda/camunda/refs/tags/{zeebe_proto_version}/zeebe/gateway-protocol/src/main/proto/gateway.proto"

    try:
        print(f"Downloading proto file from {proto_url}")
        proto_content = requests.get(proto_url, timeout=5)
        proto_content.raise_for_status()

        with proto_file.open("wb") as tmpfile:
            tmpfile.write(proto_content.content)

            grpc_tools_protoc_main(
                [
                    "--proto_path=.",
                    "--python_out=.",
                    "--mypy_out=.",
                    "--grpc_python_out=.",
                    "--mypy_grpc_out=.",
                    os.path.relpath(tmpfile.name),
                ]
            )
        proto_file.unlink()

    except requests.exceptions.HTTPError as err:
        print(f"HTTP Error occurred: {err}")
    except requests.exceptions.RequestException as err:
        print(f"Error occurred: {err}")


if __name__ == "__main__":
    main()
