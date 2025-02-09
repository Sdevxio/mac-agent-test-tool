"""Script to generate proto files with correct imports."""
import os
import sys
from grpc_tools import protoc


def generate_protos():
    """Generate proto files with correct imports."""
    # Get the absolute path to the proto file
    proto_file = os.path.abspath("proto/file_service.proto")
    output_dir = os.path.abspath("src/fileservice")

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Generate proto files
    protoc.main([
        'grpc_tools.protoc',
        f'--proto_path={os.path.dirname(proto_file)}',
        f'--python_out={output_dir}',
        f'--grpc_python_out={output_dir}',
        proto_file
    ])

    # Fix imports in generated files
    grpc_file = os.path.join(output_dir, 'file_service_pb2_grpc.py')
    if os.path.exists(grpc_file):
        with open(grpc_file, 'r') as f:
            content = f.read()

        # Fix the import statement
        content = content.replace(
            'import file_service_pb2 as file__service__pb2',
            'from . import file_service_pb2 as file__service__pb2'
        )

        with open(grpc_file, 'w') as f:
            f.write(content)

        print("Successfully generated and fixed proto files")
    else:
        print("Error: Generated files not found")
        sys.exit(1)


if __name__ == '__main__':
    generate_protos()