import os
import pathlib

import requests
from grpc_tools.protoc import main as grpc_tools_protoc_main

zeebe_proto_version = "8.6.6"


def generate_proto():
    proto_dir = pathlib.Path("pyzeebe/proto")
    proto_file = proto_dir / "gateway.proto"
    for path in proto_dir.glob("*pb2*"):
        os.remove(path)

    proto_url = f"https://raw.githubusercontent.com/camunda/camunda/refs/tags/{zeebe_proto_version}/zeebe/gateway-protocol/src/main/proto/gateway.proto"
    proto_content = requests.get(proto_url, allow_redirects=True)
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


if __name__ == "__main__":
    generate_proto()
