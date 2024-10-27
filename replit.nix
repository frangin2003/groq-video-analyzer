{ pkgs }: {
    deps = [
      pkgs.xsimd
      pkgs.pkg-config
      pkgs.libxcrypt
      pkgs.imagemagickBig
      pkgs.ffmpeg-full
      pkgs.libsndfile
      pkgs.python310
      pkgs.python310Packages.pip
      pkgs.nodejs-18_x
      pkgs.nodePackages.npm
      pkgs.opencv4
      pkgs.stdenv.cc.cc.lib
      pkgs.zlib
      pkgs.glib
    ];
    env = {
        PYTHONBIN = "${pkgs.python310}/bin/python3.10";
        LANG = "en_US.UTF-8";
        LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
            pkgs.stdenv.cc.cc.lib
            pkgs.zlib
            pkgs.glib
        ];
    };
}