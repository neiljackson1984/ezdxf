# Copyright (c) 2020, Manfred Moitzi
# License: MIT License
import time
import random

from ezdxf.math.linalg import (
    Matrix,
    gauss_vector_solver,
    LUDecomposition,
    gauss_matrix_solver,
    gauss_jordan_solver,
    gauss_jordan_inverse,
)


def random_matrix(rows, cols):
    return Matrix.reshape(
        items=(random.random() for _ in range(rows * cols)), shape=(rows, cols)
    )


SIZE = 200
CYCLES = 5

random.seed = 0
RANDOM_GAUSS_MATRIX_1 = random_matrix(rows=SIZE, cols=SIZE)
B1_VECTOR = [random.random() for _ in range(SIZE)]
B2_VECTOR = [random.random() for _ in range(SIZE)]
B3_VECTOR = [random.random() for _ in range(SIZE)]

B_MATRIX = Matrix()
B_MATRIX.append_col(B1_VECTOR)
B_MATRIX.append_col(B2_VECTOR)
B_MATRIX.append_col(B3_VECTOR)


def profile_gauss_vector_solver(count):
    for _ in range(count):
        gauss_vector_solver(RANDOM_GAUSS_MATRIX_1, B1_VECTOR)


def profile_gauss_matrix_solver(count):
    for _ in range(count):
        gauss_matrix_solver(RANDOM_GAUSS_MATRIX_1, B_MATRIX)


def profile_gauss_jordan_solver(count):
    for _ in range(count):
        gauss_jordan_solver(RANDOM_GAUSS_MATRIX_1, B_MATRIX)


def profile_LU_vector_solver(count):
    for _ in range(count):
        lu = LUDecomposition(RANDOM_GAUSS_MATRIX_1)
        lu.solve_vector(B1_VECTOR)


def profile_LU_matrix_solver(count):
    for _ in range(count):
        lu = LUDecomposition(RANDOM_GAUSS_MATRIX_1)
        lu.solve_matrix(B_MATRIX)


def profile_gauss_jordan_inverse(count):
    for _ in range(count):
        gauss_jordan_inverse(RANDOM_GAUSS_MATRIX_1)


def profile_LU_decomposition_inverse(count):
    for _ in range(count):
        LUDecomposition(RANDOM_GAUSS_MATRIX_1).inverse()


def profile(text, func, *args):
    t0 = time.perf_counter()
    func(*args)
    t1 = time.perf_counter()
    print(f"{text} {t1 - t0:.3f}s")


print(f"Profiling a random {SIZE}x{SIZE} Matrix, 5x each task:")
profile(
    "Gauss-Jordan matrix solver - 3 vectors: ", profile_gauss_jordan_solver, 5
)
profile("Gauss-Jordan inverse: ", profile_gauss_jordan_inverse, 5)
profile(
    "Gauss elimination vector solver - 1 vector : ",
    profile_gauss_vector_solver,
    5,
)
profile(
    "Gauss elimination matrix solver  - 3 vectors: ",
    profile_gauss_matrix_solver,
    5,
)
profile(
    "LU decomposition vector solver - 1 vector: ", profile_LU_vector_solver, 5
)
profile(
    "LU decomposition matrix solver - 3 vectors: ", profile_LU_matrix_solver, 5
)
profile("LU decomposition inverse: ", profile_LU_decomposition_inverse, 5)
