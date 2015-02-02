from fabric.api import local


def test(test=''):
    """ Run python tests """
    local('nosetests %s --with-coverage --cover-package=landsat' % test)
