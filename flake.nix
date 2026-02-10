{
  description = "Sinter project with custom Dedalus";
  
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };
  
  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
        
        snowmicropyn = pkgs.python312Packages.callPackage ./nixpkgs/snowmicropyn.nix {};
      in {
        packages.snowmicropyn = snowmicropyn;
        packages.default = snowmicropyn;
        
        devShells.default = import ./shell.nix { 
          inherit pkgs; 
          snowmicropyn = snowmicropyn;
        };
      });
}