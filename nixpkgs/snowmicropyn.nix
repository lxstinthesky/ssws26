{ lib
, buildPythonPackage
, fetchFromGitHub
, setuptools
, wheel
, numpy
, pandas
, python312
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
  ];

  buildInputs = [
  ];

  propagatedBuildInputs = [
    pandas
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