from fabric.api import local


def test(test=''):
    """ Run python tests """
    local('nosetests %s' % test)
