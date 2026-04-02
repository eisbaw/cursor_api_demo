# Cursor gRPC Interface Definitions

This directory contains reverse-engineered gRPC `.proto` files derived from the minified JavaScript source code of the Cursor IDE.

## Purpose

The primary purpose of these definitions is to facilitate the inspection and understanding of the data exchanged between the Cursor IDE and its backend services. By compiling these `.proto` files, developers and researchers can:

- Utilize tools like Charles Proxy (or similar network monitoring utilities) to view and analyze the gRPC messages in a human-readable format.
- Gain insights into the API structure and data models used by Cursor.
- Potentially build custom tools or integrations that interact with the Cursor backend (use with caution and respect aiserver.v1's terms of service).

## Usage

1.  **Compilation**: You will need the Protocol Buffer compiler (`protoc`) and the necessary gRPC plugins for your language of choice (e.g., Python, Go, Java). Compile the `.proto` files to generate the corresponding gRPC client and server stubs, and message classes.
    *   Example for Python:
        ```bash
        python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. server_chat.proto server_config.proto server_stream.proto server_full.proto
        ```

2.  **Proxy Setup**: Configure Charles Proxy (or your preferred tool) to intercept traffic from the Cursor IDE. You may need to install Charles' SSL certificate in your system's trust store to decrypt HTTPS traffic.

3.  **Viewing Data**: Once the proxy is set up and Cursor is running, you should be able to see the gRPC requests and responses. If your proxy supports gRPC message parsing (Charles does with the appropriate viewers), the compiled `.proto` definitions will allow it to decode the protobuf messages into a structured, readable format.

## Disclaimer

-   These `.proto` files are based on reverse engineering and may not be complete, entirely accurate, or up-to-date with the latest version of the Cursor IDE.
-   Use this information responsibly and ethically. Do not use it to abuse services or violate any terms of service. 