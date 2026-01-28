{ pkgs ? import (fetchTarball "https://github.com/NixOS/nixpkgs/archive/nixos-unstable.tar.gz") {
    config.allowUnfree = true;
  }
}:

pkgs.mkShell {
  buildInputs = [
    pkgs.code-cursor
  ];
}
