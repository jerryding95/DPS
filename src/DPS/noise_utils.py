import numpy as np
from numpy.linalg import inv
from DPS.config import *

class kalman_1d:
	def __init__(self, state, std, noise):
		self._est_state = state
		self._var = std**2
		self._noise = noise
		self._predict()
		return

	def _predict(self):
		self._pred_state = self._est_state
		self._var += self._noise
		return

	def _measure(self, val, std):
		self._val = val
		self._uncertainty = std**2
		return

	def _update(self):
		self._KG = self._var / (self._var + self._uncertainty)
		self._est_state = self._pred_state + self._KG * (self._val - self._pred_state)
		self._var = (1 - self._KG) * self._var
		return

	def iterate(self, val, std):
		self._measure(val, std)
		self._update()
		self._predict()
		print(self._val,self._est_state,self._pred_state,self._KG,self._var)
		return

	def est_state(self):
		return self._est_state

	def pred_state(self):
		return self._pred_state 

class kalman_md:
	def __init__(self, state, std, noise, dt):

		self._dt = dt
		self._shape = np.array(state).shape
		self._length = len(np.array(state).ravel())
		self._est_state = np.array(state).reshape((self._length, 1))

		# Build process noise matrix
		self._noise = np.identity(self._length)*(noise**2)
		
		# Build state trasition matrix
		self._state_tr_mat = np.identity(self._length)
		
		# Build covariance extrapolation matrix
		self._cov_extrpl_mat = np.identity(self._length)*(std**2)

		# Build observation matrix
		self._ob_mat = np.identity(self._length)

		self._predict()

	def _predict(self):
		self._pred_state = self._est_state
		self._cov_extrpl_mat += self._noise
		return

	def _measure(self, val, std):
		self._val =  self._ob_mat @ np.array(val).reshape((self._length,1))
		if type(std) is np.ndarray:
			self._uncertainty = std@std
		else:
			self._uncertainty = np.identity(self._length)*(std**2)
		return

	def _update(self):
		self._KG = self._cov_extrpl_mat @ self._ob_mat.T @ \
			inv(self._ob_mat @ self._cov_extrpl_mat @ self._ob_mat.T + self._uncertainty)
		self._est_state = self._pred_state + self._KG @ (self._val - self._ob_mat @ self._pred_state)
		self._cov_extrpl_mat = (np.identity(self._length) - self._KG @ self._ob_mat) @ self._cov_extrpl_mat \
			@ (np.identity(self._length) - self._KG @ self._ob_mat).T + self._KG @ self._uncertainty @ self._KG.T
		return

	def iterate(self, val, std):
		self._measure(val, std)
		self._update()
		self._predict()
		# print(self._val,self._est_state,self._pred_state,self._KG,self._cov_extrpl_mat)
		return

	def est_state(self):
		return self._est_state.reshape(self._shape)

	def pred_state(self):
		return self._pred_state.reshape(self._shape)




