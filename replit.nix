{ pkgs }: {
  deps = [
    pkgs.imagemagickBig
    pkgs.xsimd
    pkgs.pkg-config
    pkgs.libxcrypt
    pkgs.ffmpeg-full
    pkgs.libsndfile
    pkgs.python310
    pkgs.nodejs-18_x
    pkgs.ffmpeg
    pkgs.stdenv.cc.cc.lib
    pkgs.libstdcxx5
    pkgs.gcc
  ];
  env = {
    LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
      pkgs.stdenv.cc.cc.lib
    ];
  };
}