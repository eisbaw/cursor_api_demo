{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    # Python and package management
    python312
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
