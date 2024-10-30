#!/bin/env python
#
# A simple script to create an html page with an overview of the directory tree.
# This script walks recursively the directory tree and for each sub-directory
# it creates an 'index.html' page which will contain:
# - an overview of the subdirectories
# - a dump of the text files
# - a table (currently with two items per row) with all the images scaled to
#   some predefined size (currently 400px X 300px)
#
# davide.gerbaudo@gmail.com, Jan2011
#
# -----------
# | License |    GPLv3 (http://www.gnu.org/licenses/gpl.html)
# -----------
#
# Todo:
# - add an option not to overwrite the current index.html, or to skip
#   the directories that already have an index.html file.
# - pass the hardcoded parameters on the command line.
# - indent the html based on the directory depth


import os,sys,subprocess,operator,re
import os.path
import shutil

class Directory:
    """A directory object which knows its name, parent, and has a list of daughters.
    The directory might also have a short description associated with it,
    saying shortly what its contets are."""
    def __init__(self,name,parent="None",shortDescriptionFile="shortdescription.txt",verbose=False):
        "Constructor"
        self.name_  = name
        if not parent=="None":
            self.parent_ = parent
        self.verbose_ = verbose
        self.shortDescFile_ = shortDescriptionFile
        self.shortdescription_ = ""
        self.readDescFile(self.getBasePath()+"/"+self.shortDescFile_)
        self.populateDaughterList()
    def depth(self):
        "depth in the directory tree"
        if not hasattr(self,"parent_"): return 0
        else: return self.parent_.depth()+1
    def readDescFile(self, filename):
        "Read the file containing the one-line description of the directory's contents"
        if os.path.isfile(filename):
            self.description_ = open(filename).read()
            if self.verbose_: print( self.description_) 
        elif self.verbose_:
            print( f"Directory '{self.name_}' does not have a description file '{self.shortDescFile_}'")
    def populateDaughterList(self):
        "Populate the list of daughters directories"
        self.daughters_ = []
        basepath = self.getBasePath()
        names = os.listdir(basepath)
        skipNames = ["root-files","pdf-files","C-files"]
        for name in names:
            if os.path.isdir(basepath+'/'+name):
                if name in skipNames:
                    print( "Skipping " + name)
                    continue
                self.daughters_.append(Directory(name,self,self.shortDescFile_,self.verbose_))
        self.daughters_.sort(key=operator.attrgetter('name_'))
        if self.verbose_:
            print( "%s contains %d directories" % (self.name_,len(self.daughters_)))
    def getBasePath(self):
        "Return a basepath by asking the parents where we are"
        if not hasattr(self,"parent_"):
            return "./"
        else:
            return self.parent_.getBasePath()+"/"+self.name_
    def htmlSubDirectoryTree(self,relativeTo=None, isFirstCall=False):
        """Print an html unnumbered list showing the subdirectories of this directory.
        If relativeTo=="", the links will be relative to this directory.
        Otherwise they will be relative to the provided basepath."""
        if self.verbose_:
            print( "calling %s.htmlSubDirectoryTree " % (self.name_))
        text = ""
        # if this dir does not have a parent, then it needs to open an 'ul' on its own
        if isFirstCall:
            text +=  "<nav>\n"
        if not hasattr(self,"parent_"):
            text +=  "<ul>\n"
        if hasattr(self, "daughters_") and len(self.daughters_):
            text += "<ul>\n"
            if self.verbose_:
                print( f"{self.name_}.htmlSubDirectoryTree(relativeTo={relativeTo})")
            for daughter in self.daughters_:
                text += "<li>\n"
                target=""
                label=""
                if not relativeTo:
                    target="%s/index.html"%daughter.name_
                    label=daughter.name_
                else:
                    target="%s/%s/index.html"%(relativeTo,daughter.name_)
                    label=daughter.name_
                ## UGLY WAY TO FIX THE PROBLEM WITH THE DAUGHTER LINKS
                if not ".//"in target:
                    tmp=target.split("/")
                    if len(tmp)>2:
                        target=target.split("/")[1:len(tmp)]
                        target="/".join(target)
                ########################
                if self.verbose_:print( f"adding '{label}' --> '{target}'")
                text += f"<a href=\"{target}\">{label}</a>\n"
                if hasattr(daughter,"description_") and len(daughter.description_):
                    text += daughter.description_
                text += "</li>\n"
                # when we are done with the 1st gen daughters, do the same recursively
                relPath=""
                if not hasattr(self,"parent_"):
                    relPath="%s/%s"%(self.name_,daughter.name_)
                elif not relativeTo:
                    relPath="%s/%s"%(self.name_,daughter.name_)
                else:
                    relPath="%s/%s"%(relativeTo,daughter.name_)
                if self.verbose_:
                    print( "calling htmlSubDirectoryTree for daughter '%s' with relativeTo='%s'"\
                        %\
                        (daughter.name_, relPath))
                text += daughter.htmlSubDirectoryTree(relPath, False)
            text += "</ul>\n"
        # if this dir does not have a parent, then it needs to close an 'ul' on its own
        if not hasattr(self,"parent_"):
            text +=  "</ul>\n"
        if isFirstCall:
            text +=  "</nav>\n"
        return text

    def htmlHeader(self):
        "Print the html header"
        header= '\n'.join(['<!doctype html>',
                           '<html>',
                           '<head>',
                           '   <meta charset="utf-8">',
                           '   <title>Directory tree</title>'
                          ])
        styleline = '   <link rel="stylesheet" href="'
        for i in range(self.depth()):
            styleline+='../'
        styleline += 'style.css" />\n'
        header += styleline
        header += '\n'.join(['<!-- Generated with createHtmlOverview.py -->',
                             '</head>',
                             '<body>',
                             '<header>',
                             '  <form id="filterbar">',
                             '    <p>',
                             '    <label for="filter">Filter Images</label> : ',
                             '    <input type="search" name="filter" id="filter">',
                             '    </p>',
                             '  </form>',
                             '</header>'
                            ])
        return header
    def htmlFooter(self):
        "Print the html footer"
        return '\n'.join(['</body>',
                          '</html>'])
    def findImages(self):
        "Find the images in this directory"
        baseExtension = "png"
        imgExtensions = ["eps", "pdf", "root"]
        imgFiles = []
        files = os.listdir(self.getBasePath())
        files.sort()
        for file in files:
            if file.count(baseExtension) and not file.count("No such file"):
                row = [file]
                for ext in imgExtensions:
                    row.append(file.replace("."+baseExtension, "."+ext) in files)
                imgFiles.append(row)
        return imgFiles
    def findLinkFiles(self):
        "find the txt files in this directory"
        txtExtensions = ["tex"]
        txtFiles = []
        files = os.listdir(self.getBasePath())
        for ext in txtExtensions:
            for file in files:
                if file.count(ext) \
                       and not file.count("No such file") \
                       and not file == self.shortDescFile_:
                    txtFiles.append(file)
        return txtFiles
    def findTxtFiles(self):
        "find the txt files in this directory"
        txtExtensions = ["txt"]
        txtFiles = []
        files = os.listdir(self.getBasePath())
        for ext in txtExtensions:
            for file in sorted(files):
                if file.count(ext) \
                       and not file.count("No such file") \
                       and not file == self.shortDescFile_:
                    txtFiles.append(os.path.join(self.getBasePath(),file))
        return txtFiles
    def getImgTable(self, nColumns = 2):
        "Provide an html table showing the images of this directory"
        htmlBody='  <section id="images">\n'
        htmlBody+='  </section>\n'
        htmlBody+='  <script language="JavaScript" type="text/JavaScript">\n'
        htmlBody+='  var files =[\n'
        imgFiles = self.findImages()
        for img in imgFiles:
            htmlBody+='     ["'+img[0]+'"'
            for ext in range(1,len(img)):
                htmlBody+=','+str(img[ext]).lower()
            htmlBody+='],\n'
        htmlBody+='  ];'
        htmlBody+='  </script>\n'
        htmlBody+='  <script src="'
        for i in range(self.depth()):
            htmlBody+='../'
        htmlBody+='table.js"></script>\n'
        print( "%s %d images" % (self.name_,len(imgFiles)))
        return htmlBody
    def getLinkFilesDump(self):
        "Get a preformatted dump of the txt files in this directory"
        txtFiles = self.findLinkFiles()
        text = ""
        if len(txtFiles)>0:
            for txtFile in txtFiles:
                text += "<a href=\" %s \">" % txtFile
                text += txtFile
                text += "</a><br>"
        return text
    def getTxtFilesDump(self):
        "Get a preformatted dump of the txt files in this directory"
        txtFiles = self.findTxtFiles()
        text = ""
        if len(txtFiles)>0:
            for txtFile in txtFiles:
                text += "<pre>"
                text += subprocess.getoutput("cat %s" % txtFile)
                text += "</pre>"
        return text
    def createHtmlIndex(self, outfile="index.html", nColumns=2):
        """This function creates an index.html page with (in this order):
        - a list of the subdirectories
        - a dump of the txt files in this directory
        - a table with all the images
        This function is also called recursively for all subdirectories"""        
        try:
            file = open(self.getBasePath()+"/"+outfile, 'w')
        except OSError:
            print ("WARNING: No permission to write ",self.getBasePath()+"/"+outfile)
        else:

            file.write(self.htmlHeader()+"\n")
            file.write(self.htmlSubDirectoryTree(self.name_, True)+"\n")
            file.write(self.getTxtFilesDump()+"\n")
        #        file.write(self.getLinkFilesDump()+"\n")
            file.write(self.getImgTable(nColumns)+"\n")
            file.write(self.htmlFooter()+"\n")
            file.close()
            if hasattr(self,"daughters_"):
                for daughter in self.daughters_:
                    daughter.createHtmlIndex(nColumns = nColumns)

        # copy showROOT in all cases
        scriptPath = os.path.dirname(sys.argv[0])
        shutil.copy(scriptPath+"/showROOT.html", self.getBasePath())
        # If top directory, copy javascript and style
        if not hasattr(self,"parent_"):
            shutil.copy(scriptPath+"/table.js", self.getBasePath())
            shutil.copy(scriptPath+"/style.css", self.getBasePath())

if __name__ == '__main__':
    topDirPath = "./"
    if len(sys.argv) == 2:
        topDirPath = sys.argv[1]
    nColumns = 2
    if len(sys.argv) == 3:
        nColumns = int(sys.argv[2])
    topDir = Directory(topDirPath,verbose=False)
    topDir.createHtmlIndex(nColumns = nColumns)
