
Vagrant.configure(2) do |config|
  config.vm.box = "hashicorp/precise64"

  config.vm.provider "virtualbox" do |v|
    v.memory = 2064
    v.cpus = 2
  end

  config.vm.provision "shell", inline: <<-SHELL
    apt-get update
    apt-get install python-software-properties -y
    add-apt-repository -y ppa:ubuntugis/ppa
    apt-get update -qq
    apt-get install -y build-essential python-dev python-pip libgdal1h gdal-bin libgdal-dev libcurl4-gnutls-dev
    wget http://repo.continuum.io/miniconda/Miniconda-latest-Linux-x86_64.sh -O miniconda.sh
    chmod +x miniconda.sh
    ./miniconda.sh -b
    export PATH=/root/miniconda/bin:$PATH
    chmod 740 /root
    chown -R vagrant:vagrant /root/miniconda
    echo export PATH=/root/miniconda/bin:\$PATH >> /home/vagrant/.profile
    conda update --yes conda
  # The next couple lines fix a crash with multiprocessing on Travis and are not specific to using Miniconda
    sudo rm -rf /dev/shm
    sudo ln -s /run/shm /dev/shm

    conda install --yes -c https://conda.binstar.org/osgeo gdal
    conda install --yes numpy scikit-image requests nose dateutil

    pip install --install-option="--no-cython-compile" cython
    pip install -r /vagrant/requirements/travis.txt
    cd /vagrant
    nosetests

  SHELL
end
