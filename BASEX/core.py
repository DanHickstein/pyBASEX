#!/usr/bin/python

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from time import time
import os.path

import numpy as np
from scipy.ndimage import median_filter, gaussian_filter, map_coordinates

from .basis import generate_basis_sets


######################################################################
# PyBASEX - A Python BASEX implementation
# Dan Hickstein - University of Colorado Boulder
# danhickstein@gmail.com
#
# This is adapted from the BASEX Matlab code provided by the Reisler group.
#
# Please cite: "The Gaussian basis-set expansion Abel transform method"
# V. Dribinski, A. Ossadtchi, V. A. Mandelshtam, and H. Reisler,
# Review of Scientific Instruments 73, 2634 (2002).
#
# Version 0.3 - 2015-02-01
#   Added documentation
# Version 0.2 - 2014-10-09
#   Adding a "center_and_transform" function to make things easier
# Versions 0.1 - 2012
#   First port to Python
#
#
# To-Do list:
#
#   I took all of the linear algebra straight from the Matlab program. It's
#   a little hard to compare with the Rev. Sci. Instrum. paper. It would be
#   nice to clean this up so that it's easier to follow along with the paper.
#
#   Currently, this program just uses the 1000x1000 basis set generated using
#   the Matlab implementation of BASEX. It would be good to port the basis set
#   generating functions as well. This would give people the flexibility to use
#   different sized basis sets. For example, some image may need higher resolution
#   than 1000x1000, or, transforming larger quantities of low-resolution images
#   may be faster with a 100x100 basis set.
#
########################################################################




class BASEX(object):

    def __init__(self, n=101, nbf=200, basis_dir='./', verbose=True,
                        calc_speeds=False):
        """ Initalize the BASEX class, preloading or generating the basis set.

        Parameters:
        -----------
          - N : odd integer: Abel inverse transform will be performed on a `n x n`
            area of the image
          - nbf: integer: number of basis functions ?
          - basis_dir : path to the directory for saving / loading the basis set coefficients.
          - verbose: Set to True to see more output for debugging
          - calc_speeds: determines if the speed distribution should be calculated

        """
        n = 2*(n//2) + 1 # make sure n is odd

        self.verbose = verbose
        self.calc_speeds = calc_speeds

        self.n = n
        self.nbf = nbf

        if self.verbose:
            t1 = time()


        basis_name = "basex_basis_{}_{}.npy".format(n, nbf)
        path_to_basis_file = os.path.join(basis_dir, basis_name)
        if os.path.exists(path_to_basis_file):
            if self.verbose:
                print('Loading basis sets...           ')
            left, right, M, Mc = np.load(path_to_basis_file)

        else:
            if self.verbose:
                print('Suitable basis sets not found...')

            M, Mc = generate_basis_sets(n, nbf, verbose=verbose)
            left, right = get_left_right_matrices(M, Mc)

            np.save(path_to_basis_file, (left, right, M, Mc))
            print('Basis set saved for later use to,')
            print(' '*10 + '{}'.format(path_to_basis_file))


        self.left, self.right, self.M, self.Mc = left, right, M, Mc



        if self.verbose:
            print('{:.2f} seconds'.format((time()-t1)))


    def _basex_transform(self, rawdata):
        """ This is the core function that does the actual transform
         INPUTS:
          rawdata: a 1000x1000 numpy array of the raw image.
               Must use this size, since this is what we have generated the coefficients for.
               If your image is larger you must crop or downsample.
               If smaller, pad with zeros outside. Just use the "center_image" function.
          verbose: Set to True to see more output for debugging
          calc_speeds: determines if the speed distribution should be calculated

         RETURNS:
          IM: The abel-transformed image, 1000x1000.
              This is a slice of the 3D distribution
          speeds: (optional) a array of length=500 of the 1D distribution, integrated over all angles
        """
        rawdata = rawdata.view(np.matrix)
        left, right, M, Mc = self.left, self.right, self.M, self.Mc

        # ### Reconstructing image  - This is where the magic happens###
        if self.verbose:
            print('Reconstructing image...         ')
            t1 = time()

        Ci = (left*rawdata)*right
        # P = dot(dot(Mc,Ci),M.T) # This calculates the projection, which should recreate the original image
        IM = (Mc*Ci)*Mc.T

        if self.verbose:
            print('%.2f seconds' % (time()-t1))

        if self.calc_speeds:
            speeds = self.calculate_speeds(IM)
            return IM, speeds
        else:
            return IM


    def __call__(self, data, center,
                             median_size=0, gaussian_blur=0, post_median=0,
                             symmetrize=False):
        """ This is the main function that center the image, blurs the image (if desired)
         and completes the BASEX transform.

         Inputs:
         data - a NxN numpy array where N is larger than 1000.
                If N is smaller than 1000, zeros will we added to the edges on the image.
         center - the center of the image in (x,y) format
         median_size - size (in pixels) of the median filter that will be applied to the image before
                       the transform. This is crucial for emiminating hot pixels and other
                       high-frequency sensor noise that would interfere with the transform
         gaussian_blur - the size (in pixels) of the gaussian blur applied before the BASEX tranform.
                         this is another way to blur the image before the transform.
                         It is normally not used, but if you are looking at very broad features
                         in very noisy data and wich to apply an aggressive (large radius) blur
                         (i.e., a blur in excess of a few pixels) then the gaussian blur will
                         provide better results than the median filter.
         post_median - this is the size (in pixels) of the median blur applied AFTER the BASEX transform
                       it is not normally used, but it can be a good way to get rid of high-frequency
                       artifacts in the transformed image. For example, it can reduce centerline noise.
         verbose - Set to True to see more output for debugging
         calc_speeds - determines if the speed distribution should be calculated
        """

        image = center_image(data, center=center, n=self.n)

        if symmetrize:
            #image = apply_symmetry(image)
            raise NotImplementedError

        if median_size>0:
            image = median_filter(image,size=median_size)

        if gaussian_blur>0:
            image = gaussian_filter(image,sigma=gaussian_blur)

        #Do the actual transform
        res = self._basex_transform(image)

        if self.calc_speeds:
            recon, speeds = res
        else:
            recon = res

        if post_median > 0:
            recon = median_filter(recon, size=post_median)

        if self.calc_speeds:
            return recon, speeds
        else:
            return recon



    def calculate_speeds(self, IM):
        """ Generating the speed distribution """

        IM = IM.view(np.ndarray)

        if self.verbose:
            print('Generating speed distribution...')
            t1 = time()

        nx,ny = np.shape(IM)
        xi = np.linspace(-100, 100, nx)
        yi = np.linspace(-100, 100, ny)
        X,Y = np.meshgrid(xi,yi)

        polarIM, ri, thetai = reproject_image_into_polar(IM)

        speeds = np.sum(polarIM, axis=1)
        speeds = speeds[:500] #Clip off the corners

        if self.verbose:
            print('%.2f seconds' % (time()-t1))
        return speeds


def center_image(data, center, n):
    """ This centers the image at the given center and makes it of size n by n
     We cannot use larger images without making new coefficients, which I don't know how to do """
    Nh,Nw = data.shape
    cx, cy = np.asarray(center, dtype='int')
    im = np.zeros((2*n,2*n))
    im[n-cy:n-cy+Nh, n-cx:n-cx+Nw] = data
    #im = im[499:1500,499:1500]
    n_2 = n//2
    im = im[ n_2:n+n_2, n_2:n+n_2]
    return im


def get_left_right_matrices(M, Mc):
    left = (Mc.T * Mc).I * Mc.T #Just making things easier to read
    q=1;
    NBF=np.shape(M)[1] # number of basis functions
    E = np.identity(NBF)*q  # Creating diagonal matrix for regularization. (?)
    right = M * (M.T*M + E).I
    return left, right


# This section is to get the speed distribution.
# The original matlab version used an analytical formula to get the speed distribution directly
# from the basis coefficients. But, the C version of BASEX uses a numerical method similar to
# the one implemented here. The difference between the two methods is negligable.

# I got these next two functions from a stackoverflow page and slightly modified them.
# http://stackoverflow.com/questions/3798333/image-information-along-a-polar-coordinate-system
# It is possible that there is a faster way to get the speed distribution.
# If you figure it out, pease let me know! (danhickstein@gmail.com)
def reproject_image_into_polar(data, origin=None):
    """Reprojects a 3D numpy array ("data") into a polar coordinate system.
    "origin" is a tuple of (x0, y0) and defaults to the center of the image.
    """
    ny, nx = data.shape[:2]
    if origin is None:
        origin = (nx//2, ny//2)

    # Determine that the min and max r and theta coords will be...
    x, y = index_coords(data, origin=origin)
    r, theta = cart2polar(x, y)

    nr = r.max()
    nt = ny//2

    # Make a regular (in polar space) grid based on the min and max r & theta
    r_i = np.linspace(r.min(), r.max(), nr)
    theta_i = np.linspace(theta.min(), theta.max(), nt)
    theta_grid, r_grid = np.meshgrid(theta_i, r_i)

    # Project the r and theta grid back into pixel coordinates
    X, Y = polar2cart(r_grid, theta_grid)
    X += origin[0] # We need to shift the origin
    Y += origin[1] # back to the lower-left corner...
    xi, yi = X.flatten(), Y.flatten()
    coords = np.vstack((xi,yi)) # (map_coordinates requires a 2xn array)

    zi = map_coordinates(data, coords)
    output = zi.reshape((nr,nt))
    return output, r_i, theta_i


def index_coords(data, origin=None):
    """Creates x & y coords for the indicies in a numpy array "data".
    "origin" defaults to the center of the image. Specify origin=(0,0)
    to set the origin to the lower left corner of the image.
    """
    ny, nx = data.shape[:2]
    if origin is None:
        origin_x, origin_y = nx // 2, ny // 2
    else:
        origin_x, origin_y = origin
    x, y = np.meshgrid(np.arange(nx), np.arange(ny))
    x -= origin_x
    y -= origin_y
    return x, y

def cart2polar(x, y):
    """
    Transform carthesian coordinates to polar
    """
    r = np.sqrt(x**2 + y**2)
    theta = np.arctan2(y,x)
    return r, theta

def polar2cart(r, theta):
    """
    Transform polar coordinates to carthesian
    """
    x = r * np.sin(theta)
    y = r * np.cos(theta)
    return x, y
