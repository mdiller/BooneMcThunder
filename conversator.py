import os
import openai
import functools
from concurrent.futures import ThreadPoolExecutor

class Conversator:
	def __init__(self, api_key, loop):
		openai.api_key = api_key
		self.messages = []
		self.loop = loop

	def input_system(self, message):
		self.messages.append({"role": "system", "content": message})

	def input_user(self, message):
		self.messages.append({"role": "user", "content": message})

	def input_self(self, message):
		self.messages.append({"role": "assistant", "content": message})
	
	def _get_response(self):
		response = openai.ChatCompletion.create(
			model="gpt-3.5-turbo",
			messages=self.messages)

		return response["choices"][0]["message"]["content"]
	
	async def get_response(self):
		response = await self.loop.run_in_executor(ThreadPoolExecutor(), self._get_response)
		self.input_self(response)
		return response
		

