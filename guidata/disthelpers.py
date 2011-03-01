# -*- coding: utf-8 -*-
#
# Copyright © 2009-2010 CEA
# Pierre Raybaut
# Licensed under the terms of the CECILL License
# (see guidata/__init__.py for details)

"""
disthelpers
-----------

The ``guidata.disthelpers`` module provides helper functions for Python 
package distribution on Microsoft Windows platforms with ``py2exe``.
"""

import sys, os, os.path as osp, shutil


def remove_build_dist(dist="dist"):
    """Remove *build* and *dist* directories
    (before building a new py2exe distribution)"""
    print "Removing 'build' and '%s' directories" % dist
    shutil.rmtree("build", ignore_errors=True)
    shutil.rmtree(dist, ignore_errors=True)


def get_changeset(path, rev=None):
    """Return Mercurial repository *path* revision number"""
    from subprocess import Popen, PIPE
    args = ['hg', 'parent']
    if rev is not None:
        args += ['--rev', str(rev)]
    p = Popen(args, stdout=PIPE, stderr=PIPE, cwd=path, shell=True)
    try:
        return p.stdout.read().splitlines()[0].split()[1]
    except IndexError:
        raise RuntimeError(p.stderr.read())


def strip_version(version):
    """Return version number with digits only
    (Windows does not support strings in version numbers)"""
    return version.split('beta')[0].split('alpha')[0].split('rc')[0]


def prepend_module_to_path(module_path):
    """
    Prepend to sys.path module located in *module_path*
    Return string with module infos: name, revision, changeset
    
    Use this function:
    1) In your application to import local frozen copies of internal libraries
    2) In your py2exe distributed package to add a text file containing the 
       returned string
    """
    if not osp.isdir(module_path):
        # Assuming py2exe distribution
        return
    sys.path.insert(0, osp.abspath(module_path))
    changeset = get_changeset(module_path)
    name = osp.basename(module_path)
    prefix = "Prepending module to sys.path"
    message = prefix+("%s [revision %s]" % (name, changeset)) \
              .rjust(80-len(prefix), ".")
    print >>sys.stderr, message
    return message

def prepend_modules_to_path(module_base_path):
    """Prepend to sys.path all modules located in *module_base_path*"""
    if not osp.isdir(module_base_path):
        # Assuming py2exe distribution
        return
    fnames = [osp.join(module_base_path, name)
              for name in os.listdir(module_base_path)]
    messages = [prepend_module_to_path(dirname)
                for dirname in fnames if osp.isdir(dirname)]
    return os.linesep.join(messages)


def remove_at_exit(fname):
    """Remove temporary file *fname* at exit"""
    import atexit
    atexit.register(os.remove, fname)


def add_module_data_files(module_name, data_dir_names, extensions, data_files,
                          copy_to_root=True):
    """
    Collect data files for module *module_name* and add them to *data_files*
    *data_dir_names*: list of dirnames, e.g. ('images',)
    *extensions*: list of file extensions, e.g. ('.png', '.svg')
    """
    print "Adding module '%s' data files (%s):" % (module_name,
                                                   ", ".join(data_dir_names))
    print "(file extensions: %s)" % ", ".join(extensions)
    module_dir = osp.dirname(__import__(module_name).__file__)
    nstrip = len(module_dir) + len(osp.sep)
    for data_dir_name in data_dir_names:
        data_dir = osp.join(module_dir, data_dir_name)
        if not osp.isdir(data_dir):
            raise IOError, "Directory not found: %s" % data_dir
        for dirpath, _dirnames, filenames in os.walk(data_dir):
            dirname = dirpath[nstrip:]
            if not copy_to_root:
                dirname = osp.join(module_name, dirname)
            pathlist = [osp.join(dirpath, f) for f in filenames
                        if osp.splitext(f)[1] in extensions]
            data_files.append( (dirname, pathlist) )
            for name in pathlist:
                print "  ", name
    translation_file = osp.join(module_dir, "locale", "fr", "LC_MESSAGES",
                                "%s.mo" % module_name)
    if osp.isfile(translation_file):
        data_files.append( (osp.join(module_name, "locale", "fr",
                                     "LC_MESSAGES"),
                            (translation_file,)) )
        print "  ", translation_file


def add_text_data_file(filename, contents, data_files):
    """Create temporary data file *filename* with *contents*
    and add it to *data_files*"""
    file(filename, 'wb').write(contents)
    data_files += [("", (filename,)),]
    remove_at_exit(filename)
    
    
def get_default_excludes():
    return ['Tkconstants', 'Tkinter', 'tcl', 'wx', '_imagingtk', 'curses',
            'PIL._imagingtk', 'ImageTk', 'PIL.ImageTk', 'FixTk', 'bsddb',
            'email', 'pywin.debugger', 'pywin.debugger.dbgcon',
            'matplotlib']
    
def get_default_includes():
    return []
    
def get_default_dll_excludes():
    return ['MSVCP90.dll', 'w9xpopen.exe', 'MSVCP80.dll', 'MSVCR80.dll']


def create_vs2008_data_files():
    """Including Microsoft Visual C++ 2008 DLLs"""    
    filelist = []
    manifest = osp.join(sys.prefix, "Microsoft.VC90.CRT.manifest")
    filelist.append(manifest)
    
    from xml.etree import ElementTree
    assembly = ElementTree.fromstring(file(manifest).read())
    assid = assembly.find("{urn:schemas-microsoft-com:asm.v1}assemblyIdentity")
    version = assid.get("version")
    arch = assid.get("processorArchitecture")
    key = assid.get("publicKeyToken")

    vc_str = '%s_Microsoft.VC90.CRT_%s_%s' % (arch, key, version)
    winsxs = osp.join(os.environ['windir'], 'WinSxS')
    for fname in os.listdir(winsxs):
        path = osp.join(winsxs, fname)
        if osp.isdir(path) and fname.startswith(vc_str):
            for dllname in os.listdir(path):
                filelist.append(osp.join(path, dllname))
            break

    print create_vs2008_data_files.__doc__, ":"
    for name in filelist:
        print "  ", name
        
    return [("Microsoft.VC90.CRT", filelist),]

    
def add_modules(module_names, data_files, includes, excludes, vs2008=True):
    """Include module *module_name*"""
    for module_name in module_names:
        if module_name == 'PyQt4':
            includes += ['sip', 'PyQt4.Qt', 'PyQt4.QtSvg', 'PyQt4.QtNetwork']
            
            import PyQt4
            pyqt_path = osp.dirname(PyQt4.__file__)
            
            # Configuring PyQt4
            conf = os.linesep.join(["[Paths]", "Prefix = .", "Binaries = ."])
            add_text_data_file('qt.conf', conf, data_files)
            
            # Including plugins (.svg icons support, QtDesigner support, ...)
            if vs2008:
                vc90man = "Microsoft.VC90.CRT.manifest"
                shutil.copy(osp.join(sys.prefix, vc90man), vc90man)
                man = file(vc90man, "r").read().replace('<file name="',
                                            '<file name="Microsoft.VC90.CRT\\')
                file(vc90man, 'w').write(man)
            for dirpath, _, filenames in os.walk(osp.join(pyqt_path,
                                                          "plugins")):
                filelist = [osp.join(dirpath, f) for f in filenames
                            if osp.splitext(f)[1] in ('.dll', '.py')]
                if vs2008 and [f for f in filelist
                               if osp.splitext(f)[1] == '.dll']:
                    # Where there is a DLL build with Microsoft Visual C++ 2008,
                    # there must be a manifest file as well...
                    # ...congrats to Microsoft for this great simplification!
                    filelist.append(vc90man)
                data_files.append( (dirpath[len(pyqt_path)+len(os.pathsep):],
                                    filelist) )
            remove_at_exit(vc90man)
            
            # Including french translation
            data_files.append( ('translations',
                                (osp.join(pyqt_path, "translations",
                                          "qt_fr.qm"),)) )
        
        elif module_name == 'matplotlib':
            if 'matplotlib' in excludes:
                excludes.pop(excludes.index('matplotlib'))
            includes += ['matplotlib.numerix.ma',
                         'matplotlib.numerix.fft',
                         'matplotlib.numerix.linear_algebra',
                         'matplotlib.numerix.mlab',
                         'matplotlib.numerix.random_array']
            add_module_data_files('matplotlib', ('mpl-data',),
                                  ('.conf', '.glade', '', '.png', '.svg',
                                   '.xpm', '.ppm', '.npy', '.afm', '.ttf'),
                                  data_files)
            #TODO: adding matplotlib's data directory
        
        elif module_name == 'h5py':
            import h5py
            for attr in ['_stub', '_sync', 'utils', '_conv', '_proxy']:
                if hasattr(h5py, attr):
                    includes.append('h5py.%s' % attr)
        
        elif module_name in ('docutils', 'rst2pdf', 'sphinx'):
            includes += ['docutils.writers.null',
                         'docutils.languages.en',
                         'docutils.languages.fr']
            if module_name == 'rst2pdf':
                add_module_data_files("rst2pdf", ("styles",),
                                      ('.json', '.style'),
                                      data_files, copy_to_root=True)
        
        else:
            try:
                # guidata, guiqwt, ...
                add_module_data_files(module_name,
                                      ("images",), ('.png', '.svg'),
                                      data_files, copy_to_root=False)
            except IOError:
                raise RuntimeError("Module not supported: %s" % module_name)
