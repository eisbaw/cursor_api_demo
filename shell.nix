{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    # Python and package management
    python312
    python312Packages.protobuf
    python312Packages.httpx
    python312Packages.h2
    uv
    
    # Development tools
    just
    ripgrep
    jq
    git
    
    # Optional: for building native extensions
    gcc
    pkg-config
    
    # Optional: for protobuf compilation
    protobuf
  ];
}
