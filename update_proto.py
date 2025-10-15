# /// script
# requires-python = ">=3.11,<3.14"
# dependencies = [
#   # pin version for code generation, see https://protobuf.dev/support/cross-version-runtime-guarantee/#major
#   "protobuf>=5.28,<6.0",
#   "grpcio-tools>=1.66",
#   "mypy-protobuf>=3.6",
# ]
# ///

import argparse
import os
import pathlib
from http.client import HTTPResponse
from urllib import error
from urllib.request import urlopen

from grpc_tools.protoc import main as grpc_tools_protoc_main

DEFAULT_PROTO_VERSION: str = "8.7.10"


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
        proto_content: HTTPResponse = urlopen(proto_url, timeout=5)

        with proto_file.open("wb") as tmpfile:
            tmpfile.write(proto_content.read())

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

    except error.HTTPError as err:
        print(f"HTTP Error occurred: {err}")
    except error.URLError as err:
        print(f"Error occurred: {err}")


if __name__ == "__main__":
    main()
