require "formula"

class LandsatUtil < Formula
  homepage "http://www.developmentseed.org"
  url "https://github.com/developmentseed/landsat-util/archive/v0.2.0.tar.gz"
  sha1 "522e460c7cb8c229c3bf4e3d965b0c9f5924c1e9"
  head "https://github.com/developmentseed/landsat-util.git"

  depends_on "gdal"
  depends_on "libtiff"
  depends_on "imagemagick" => "with-libtiff"
  depends_on "https://raw.githubusercontent.com/OSGeo/homebrew-osgeo4mac/master/Formula/orfeo-40.rb"

  def install
    minor = `python -c 'import sys; print(sys.version_info[1])'`.chomp
    ENV.prepend_create_path "PYTHONPATH", libexec/"lib/python2.#{minor}/site-packages"
    system "python", "setup.py", "install",
           "--prefix=#{libexec}",
           "--install-scripts=#{bin}"
    bin.env_script_all_files(libexec+"bin", :PYTHONPATH => ENV["PYTHONPATH"])
  end
end
