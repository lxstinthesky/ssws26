{ pkgs ? import <nixpkgs> {}, snowmicropyn }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    # Core Python
    python312
    snowmicropyn
    #
    (pkgs.python312.withPackages (python-pkgs: with python-pkgs; [
      numpy
      scipy
      matplotlib
      ipykernel
      ipython
      jupyter
      notebook # for vscode?
      rich # colored logging
    ]))
    
    # System libraries
    libz
  ];

  shellHook = ''
    # Make Nix packages available to Python
    export PYTHONPATH="${snowmicropyn}/${pkgs.python312.sitePackages}:$PYTHONPATH"
  '';
}