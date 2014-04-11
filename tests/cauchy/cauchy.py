""" Solves the Cauchy optimal control problem 

Reference:
Example 4, Section 7.1.1, pp 222. in J. Sundnes et al (2006). Computing the Eletrical Activity in the Heart. Springer Verlag.
"""

from dolfin import *
from dolfin_adjoint import *

try:
    import moola
except ImportError:
    import sys
    info_blue("moola bindings unavailable, skipping test")
    sys.exit(0)

res = 128
mesh = UnitSquareMesh(res, res)

dolfin.set_log_level(ERROR)
parameters['std_out_all_processes'] = False
x = triangle.x

class Bottom(SubDomain):
    def inside(self, x, on_boundary):
        return near(x[1], 0.0)

class Top(SubDomain):
    def inside(self, x, on_boundary):
        return near(x[1], 1.0)

bottom = Bottom()
top = Top()
boundaries = FacetFunction("size_t", mesh)
boundaries.set_all(0)
bottom.mark(boundaries, 1)
top.mark(boundaries, 3)
ds = Measure("ds")[boundaries]

V = FunctionSpace(mesh, "CG", 1)
W = FunctionSpace(mesh, "DG", 1)
u = Function(V, name='State')
g = Function(W, name='Control')
v = TestFunction(V)
w = TrialFunction(V)
n = FacetNormal(mesh)
h = CellSize(mesh)

def solve_pde(u, g):
    gamma = Constant(10)
    # Weak form of Laplace problem with Nitsche boundary condition.
    F = inner(grad(w), grad(v))*dx - inner(grad(w), n)*v*ds(3) - inner(grad(v), n)*(w-g)*ds(3) + gamma/h*(w-g)*v*ds(3)
    solve(lhs(F) == rhs(F), u)

# Run the forward model once to create the annotation
solve_pde(u, g)

# ========= Example settings ===============
d = cos(pi*x[0]) / cosh(pi) # Data
alpha = Constant(0)         # Regularisation multiplier
delta = Constant(2.0)       # Perturbation multiplier
d += delta*cos(5*pi*x[0])

g_ana = cos(pi*x[0])
g_ana += 3.32*10**6*delta*cos(5*pi*x[0])

J = Functional((inner(u-d, u-d))*ds(1) + alpha*g**2*ds(3))
m = SteadyParameter(g)

rf = ReducedFunctional(J, m)

problem = rf.moola_problem()
solver = moola.BFGS(tol=None, options={'gtol': 1e-11, 'maxiter': 20, 'mem_lim': 20})
#solver = moola.NewtonCG(tol=1e-200, options={'gtol': 1e-10, 'maxiter': 20, 'ncg_reltol':1e-20, 'ncg_hesstol': "default"})
g_moola = moola.DolfinPrimalVector(g)
sol = solver.solve(problem, g_moola)
g_opt = sol['Optimizer'].data

#g_opt = minimize(rf, method="L-BFGS-B", tol=1e-09, options={"xtol": 1e-100})

solve_pde(u, g_opt)
plot(d, title="Data", mesh=mesh)
plot(g_ana, title="Optimal boundary condition", mesh=mesh)
plot(u, title="Optimised solution")

print "Final J = ", assemble(inner(u-d, u-d)*ds(1))
print "||g* - g_analytic|| / ||g_analytic|| = ", (assemble((g_opt - g_ana)**2*ds(3))**0.5 / assemble(g_ana**2*ds(3))**0.5)

interactive()