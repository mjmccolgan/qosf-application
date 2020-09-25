import cirq
import math
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import minimize

# EvenBlockMoments is a method that takes a list of four angles, and four qubits
# to apply gates to. The method assembles a series of gates into a list of
# moments to be returned and appended to a central circuit. First Z gates are
# applied, followed by pairwise CZ operations. The pairwise CZ gates have the
# effect of introducing a phase flip if an two or three of the qubits in a state
# are in the 1 state.
def EvenBlockMoments(qubits, angles):
    moments = [cirq.Moment([cirq.rz(angles[i])(qubits[i]) for i in range(4)])]
    moments.append(cirq.CZ(qubits[0], qubits[1]))
    moments.append(cirq.CZ(qubits[0], qubits[2]))
    moments.append(cirq.CZ(qubits[0], qubits[3]))
    moments.append(cirq.CZ(qubits[1], qubits[2]))
    moments.append(cirq.CZ(qubits[1], qubits[3]))
    moments.append(cirq.CZ(qubits[2], qubits[3]))
    return moments

# OddBlockMoments is a method that takes a list of four angles, and four qubits
# to apply gates to. The method assembles X rotations into a moment, and returns
# that moment in a list.
def OddBlockMoments(qubits, angles):
    return [cirq.Moment([cirq.rx(angles[i])(qubits[i]) for i in range(4)])]

# RunCircuit is a method that takes an L x 8 array of angle parameters. It
# builds a circuit according to the angle specifications given, adding
# alternating even and odd moments to the circuit. It returns the simulated
# output vector from the circuit (not a measurement).
def RunCircuit(angle_array):
    # Build the circuit.
    circuit = cirq.Circuit()
    test_qubits = cirq.LineQubit.range(4)
    for i in range(len(angle_array)):
        even_angles = angle_array[i][:4]
        odd_angles = angle_array[i][4:]
        for m in EvenBlockMoments(test_qubits, even_angles):
            circuit.append(m)
        for m in OddBlockMoments(test_qubits, odd_angles):
            circuit.append(m)

    print(circuit)
    # Run it through a simulator starting with 0's.
    simulator = cirq.Simulator()
    return simulator.simulate(circuit).state_vector()

# GridSearch is a naive optimization method. It takes an array that defines the
# center of its search space, a width that describes the scope of the search,
# and a resolution with which to search the described space. This setup allows
# us to make multiple calls, narrowing in on the minimum value from a previous
# grid search. The problem with this method is that the number of angles is
# linear in the number of layers, and the amount of variables to search is
# exponential in number of grid steps per angle (width / resolution). This is
# not a feasible function to use for the nature of the problem.
def GridSearch(center_array, width, resolution, Objective):
    start_angles = [a - width / 2 for a in center_array]
    angles = start_angles[:]
    opt_val = float('inf')
    # Avoid floating point errors by slightly increasing the width.
    while angles[-1] < start_angles[-1] + width * 1.01:
        obj = Objective(np.array(angles))
        if obj < opt_val:
            opt_val = obj
            best_angles = angles[:]

        angles[0] += resolution
        for i in range(len(angles)):
            if angles[i] > start_angles[i] + width * 1.01:
                if i == len(angles) - 1:
                    break
                angles[i] = start_angles
                angles[i+1] += resolution
            else:
                break
    return best_angles, opt_val

# GeneratePlot does the heavy lifting of this task. It handles optimizing at
# each layer and generating the solution plot. The objective function is simply
# the L2 norm of phi and the output of the circuit. It is convex in the result,
# but unfortunately not in the parameters since there are trig functions needed
# to generate the result. We'll use scipy's minimize to find optimal parameters.
def GeneratePlot(max_L):
    max_L += 1
    # The random state we are trying to achieve
    phi = cirq.testing.random_superposition(dim=16)

    # This function simply returns the L2 norm of the difference of the two
    # states. It is the function we want to minimize with respect to the angles
    # theta. To use scipy's minimize, we need to pass in a 1-D array.
    def Objective(angles):
        angle_array = angles.reshape((len(angles) // 8, 8))
        return np.linalg.norm(phi - RunCircuit(angle_array))

    best_vals = []

    for L in range(2, max_L):
        # Bound angles between 0 and 2 pi. There are infinitely many solutions
        # otherwise. Scipy's minimize tends to perform better only having to 
        # search a constrained space.
        bounds = [(0, 2*math.pi) for i in range(8*L)]

        # We'll use a random guess in the interval to start optimizing. This
        # generally performs well when optimizing over a uniform start. We'll do
        # a few different random samples, to explore different areas of the
        # objective function.
        opt_val = float('inf')
        for _ in range(10):
            start_angles = np.random.uniform(low=0, high=2*math.pi, size=(8*L))
            opt = minimize(Objective, start_angles, bounds=bounds)
            if opt.fun < opt_val:
                opt_val = opt.fun
        best_vals.append(opt_val)

    title_string = "Normalized Difference Between Circuit Output and\n"
    title_string += "Target State as a Function Circuit Layers"
    plt.plot([i for i in range(1, max_L)], best_vals)
    plt.title(title_string)
    plt.xlabel("Circuit Layers")
    plt.ylabel("Distance to target")
    plt.show()
    

GeneratePlot(2)
