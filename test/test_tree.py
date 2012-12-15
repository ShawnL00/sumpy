from __future__ import division

import numpy as np
import sys
import pytools.test

import matplotlib.pyplot as pt

import pyopencl as cl
from pyopencl.tools import pytest_generate_tests_for_pyopencl \
        as pytest_generate_tests





@pytools.test.mark_test.opencl
def test_tree(ctx_getter, do_plot=False):
    ctx = ctx_getter()
    queue = cl.CommandQueue(ctx)

    #for dims in [2, 3]:
    for dims in [2]:
        nparticles = 10**5
        dtype = np.float64

        from pyopencl.clrandom import RanluxGenerator
        rng = RanluxGenerator(queue, seed=15)

        from pytools.obj_array import make_obj_array
        particles = make_obj_array([
            rng.normal(queue, nparticles, dtype=dtype)
            for i in range(dims)])

        if do_plot:
            pt.plot(particles[0].get(), particles[1].get(), "x")

        from sumpy.tree import TreeBuilder
        tb = TreeBuilder(ctx)

        queue.finish()
        print "building..."
        tree = tb(queue, particles, max_particles_in_box=30)
        print "%d boxes, testing..." % tree.nboxes

        starts = tree.box_starts.get()
        pcounts = tree.box_particle_counts.get()
        sorted_particles = np.array([pi.get() for pi in tree.particles])
        centers = tree.box_centers.get()
        levels = tree.box_levels.get()

        root_extent = tree.root_extent

        for ibox in xrange(tree.nboxes):
            lev = int(levels[ibox])
            box_size = root_extent / (1 << lev)
            el = extent_low = centers[:, ibox] - 0.5*box_size
            eh = extent_high = extent_low + box_size

            box_particle_nrs = np.arange(starts[ibox], starts[ibox]+pcounts[ibox],
                    dtype=np.intp)

            if do_plot:
                pt.plot([el[0], eh[0], eh[0], el[0], el[0]],
                        [el[1], el[1], eh[1], eh[1], el[1]], "k-")

            box_particles = sorted_particles[:,box_particle_nrs]
            good = (
                    (box_particles < extent_high[:, np.newaxis])
                    &
                    (extent_low[:, np.newaxis] <= box_particles)
                    )

            if do_plot and not good.all():
                pt.plot(
                        box_particles[0, np.where(~good)[1]],
                        box_particles[1, np.where(~good)[1]], "ro")

                pt.plot([el[0], eh[0], eh[0], el[0], el[0]],
                        [el[1], el[1], eh[1], eh[1], el[1]], "r-", lw=1)

            assert good.all(), ibox

        print "done"

        if do_plot:
            pt.gca().set_aspect("equal", "datalim")
            pt.show()









# You can test individual routines by typing
# $ python test_kernels.py 'test_p2p(cl.create_some_context)'

if __name__ == "__main__":
    # make sure that import failures get reported, instead of skipping the tests.
    import pyopencl as cl

    import sys
    if len(sys.argv) > 1:
        exec(sys.argv[1])
    else:
        from py.test.cmdline import main
        main([__file__])

# vim: fdm=marker
