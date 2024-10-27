{ pkgs }: {
  deps = [
    pkgs.python310
    pkgs.ffmpeg
    # Add system libraries
    pkgs.stdenv.cc.cc.lib
    pkgs.libstdc++
    pkgs.gcc
    # Add other potential required libraries
    pkgs.zlib
    pkgs.glib
    pkgs.libsm6
    pkgs.libxext6
    pkgs.libxrender-dev
    pkgs.libgcc-s1
  ];
  env = {
    PYTHONBIN = "${pkgs.python310}/bin/python3.10";
    LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
      pkgs.stdenv.cc.cc.lib
      "${pkgs.lib.getLib pkgs.stdenv.cc.cc}/lib64"
    ];
    PYTHONPATH = "${pkgs.python310}/lib/python3.10/site-packages";
  };
}