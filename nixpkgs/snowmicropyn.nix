{ lib
, buildPythonPackage
, fetchFromGitHub
, setuptools
, wheel
, numpy
, pandas
, pyqt5
, scikit-learn
, python312
, libsForQt5
}:

buildPythonPackage rec {  
  pname = "snowmicropyn";
  version = "1.2.1";
  format = "setuptools";

  src = fetchFromGitHub {
    owner = "slf-dot-ch";
    repo = "snowmicropyn";
    rev = "v1.2.1";
    sha256 = "sha256-B1WDZVjStckK5hJ/f2BkBY+PFVAB43J7kI1FRLB5SRM=";
  };

  nativeBuildInputs = [
    libsForQt5.qt5.qttools
    libsForQt5.qt5.wrapQtAppsHook
  ];

  buildInputs = [
  ];

  propagatedBuildInputs = [
    pandas
    pyqt5
    scikit-learn
    libsForQt5.qt5.qtbase
  ];

  nativeCheckInputs = [
  ];

  # Set environment variables for the build
  preBuild = ''
  '';

  # Skip tests for now
  doCheck = true;

  checkPhase = ''
    runHook preCheck
  '';

  

  # Wrapper script for launching the GUI with correct Qt env
  postInstall = ''
    mkdir -p $out/bin
    cat > $out/bin/pyngui <<EOF
    #!/usr/bin/env bash
    exec python3 -m snowmicropyn.pyngui.app "$@"
    EOF
    chmod +x $out/bin/pyngui
  '';

  preFixup = ''
    wrapQtApp "$out/bin/pyngui" --prefix PATH : /path/to/bin
  '';

  # Enable parallel building
  enableParallelBuilding = true;

  meta = with lib; {
    description = "A Python package to read, export and post process data (*.pnt files) recorded by SnowMicroPen, a snow penetration probe for scientifc applications developed at SLF.";
    homepage = "https://snowmicropyn.readthedocs.io/en/latest/";
    license = licenses.gpl3;
    maintainers = [ "Henrik Jentgens" ];
    platforms = platforms.linux;
  };
}