#!/usr/bin/env python3

import unittest
from sqroots import sqroots

class TestSome(unittest.TestCase):

	def test_normal1(self):
		"""Two root"""
		self.assertEqual(sqroots("1 2 0"), "0.0 -2.0")
	def test_normal2(self):
		"""One root"""
		self.assertEqual(sqroots("1 2 1"), "-1.0")

	def test_normal3(self):
		"""Zero root"""
		self.assertEqual(sqroots("1 2 3"), "")

	def test_esxception(self):
		"""Devesion by zero"""
		with self.assertRaises(ZeroDivisionError):
			sqroots("0 1 2")

	def test_attribute(self):
		"""Incorrect Attribute"""
		with self.assertRaises(AttributeError):
			sqroots(1)

	def test_value(self):
		"""Incorrect Value"""
		with self.assertRaises(ValueError):
			sqroots("jkh uhjgv uhigjvb")
