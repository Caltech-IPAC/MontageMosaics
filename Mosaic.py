import os
import sys
import shutil
import json
from IPython.display import display, clear_output

from MontagePy.main    import *
from MontagePy.archive import *


class Mosaic:

    def __init__(self, **kwargs):

        verbose            = False
        dataset            = "2MASS J"
        size               = 0.5
        resolution         = 1
        coordinateSystem   = 'Equatorial'
        workdir            = "work"
        backgroundMatching = True
        outfile            = 'mosaic.fits'


        # Arguments


        if ('location' in kwargs):
            location =  kwargs ['location']
        else:
            raise Exception('Location Required')

        if ('verbose' in kwargs):
            verbose =  kwargs ['verbose']

        if ('dataset' in kwargs):
            dataset = kwargs['dataset']

        if dataset[:4].upper() == 'WISE':
            resolution = 6.0

        if dataset[:4].upper() == 'SDSS':
            resolution = 0.4

        if ('resolution' in kwargs):
            resolution = kwargs['resolution']

        if ('size' in kwargs):
            size = kwargs['size']

        if ('coordinateSystem' in kwargs):
            coordinateSystem = kwargs['coordinateSystem']

        if ('workdir' in kwargs):
            workdir = kwargs['workdir']

        if ('outfile' in kwargs):
            outfile = kwargs['outfile']

        if ('backgroundMatching' in kwargs):
            backgroundMatching = kwargs['backgroundMatching']


        home = os.getcwd()

        os.chdir(home)


        # Clean out any old copy of the work tree, then remake it
        # and the set of the subdirectories we will need.

        try:
            shutil.rmtree(workdir)
        except:
            pass


        os.makedirs(workdir)

        os.chdir(workdir)

        os.makedirs("raw")
        os.makedirs("projected")
        os.makedirs("diffs")
        os.makedirs("corrected")


        # Create the FITS header for the mosaic.

        display("Constructing region header specification ...")
        if verbose == False:
            clear_output(wait=True)

        self.status = mHdr(location, size, size, "region.hdr",
                           resolution=resolution, csys=coordinateSystem)
        
        if self.status['status'] == 1:
            display(self.status['msg'])
            return


        # Retrieve archive images covering the region then scan
        # the images for their coverage metadata.

        display("Downloading image data ...")
        if verbose == False:
           clear_output(wait=True)

        self.status = mArchiveDownload(dataset, location, size, "raw")
        
        self.status = self.status.replace("'", '"')         # Kludge around a bug
        self.status = json.loads(self.status)               # in MontagePy code

        if self.status['status'] == 1:
            display(self.status['msg'])
            return


        display("Collecting metadata for " + str(self.status['count']) + " images ...")
        if verbose == False:
            clear_output(wait=True)

        self.status = mImgtbl("raw", "rimages.tbl")
        
        if self.status['status'] == 1:
            display(self.status['msg'])
            return


        # Reproject the original images to the  frame of the
        # output FITS header we created

        display("Reprojecting images ...")
        if verbose == False:
            clear_output(wait=True)

        self.status = mProjExec("raw", "rimages.tbl", "region.hdr", projdir="projected", quickMode=True)
        
        if self.status['status'] == 1:
            display(self.status['msg'])
            return


        display("Collecting projected image metadata ...")
        if verbose == False:
            clear_output(wait=True)

        mImgtbl("projected", "pimages.tbl")
        
        if self.status['status'] == 1:
            display(self.status['msg'])
            return


        if backgroundMatching:

            # Determine the overlaps between images (for background modeling).

            display("Determining image overlaps for background modeling ...")
            if verbose == False:
                clear_output(wait=True)

            self.status = mOverlaps("pimages.tbl", "diffs.tbl")
        
            if self.status['status'] == 1:
                display(self.status['msg'])
                return


            # Generate difference images and fit them.

            display("Analyzing " + str(self.status['count']) + " image overlaps ...")
            if verbose == False:
                clear_output(wait=True)

            self.status = mDiffFitExec("projected", "diffs.tbl", "region.hdr", "diffs", "fits.tbl")
        
            if self.status['status'] == 1:
                display(self.status['msg'])
                return


            # Model the background corrections.

            display("Modeling background corrections ...")
            if verbose == False:
                clear_output(wait=True)

            self.status = mBgModel("pimages.tbl", "fits.tbl", "corrections.tbl")
        
            if self.status['status'] == 1:
                display(self.status['msg'])
                return


            # Background correct the projected images.

            display("Applying background corrections ...")
            if verbose == False:
                clear_output(wait=True)

            self.status = mBgExec("projected", "pimages.tbl", "corrections.tbl", "corrected")
        
            if self.status['status'] == 1:
                display(self.status['msg'])
                return


            display("Collecting corrected image metadata ...")
            if verbose == False:
                clear_output(wait=True)

            self.status = mImgtbl("corrected", "cimages.tbl")
        
            if self.status['status'] == 1:
                display(self.status['msg'])
                return


            # Coadd the background-corrected, projected images.

            os.chdir(home)

            display("Coadding corrected images into final mosaic ...")
            if verbose == False:
                clear_output(wait=True)

            self.status = mAdd(workdir+"/corrected", workdir+"/cimages.tbl", workdir+"/region.hdr", outfile)
        
            if self.status['status'] == 1:
                display(self.status['msg'])
                return

        else:

            # Coadd the projected images.

            os.chdir(home)

            display("Coadding projected images into final mosaic ...")
            if verbose == False:
                clear_output(wait=True)

            self.status = mAdd(workdir+"/projected", workdir+"/pimages.tbl", workdir+"/region.hdr", outfile)
        
            if self.status['status'] == 1:
                display(self.status['msg'])
                return

        display("Final mosaic image: " + outfile)


