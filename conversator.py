import os
import openai
import functools
from concurrent.futures import ThreadPoolExecutor

MAX_TOKENS_STORED = 3300

class Conversator:
	def __init__(self, api_key, loop):
		openai.api_key = api_key
		self.messages = []
		self.token_counts = []
		self.tokens_total = 0
		self.loop = loop

	def _input_message(self, role, message):
		count = len(message.split(" "))
		self.messages.append({"role": role, "content": message})
		self.token_counts.append(count)
		self.tokens_total += count

		# make sure we don't go over the limit of tokens stored. delete non-system messages from beginning to allow for this.
		i = 0
		while self.tokens_total > MAX_TOKENS_STORED:
			if self.messages[i]["role"] == "system":
				i += 1
			else:
				self.tokens_total -= self.token_counts[i]
				del self.token_counts[i]
				del self.messages[i]

	def input_system(self, message):
		self._input_message("system", message)

	def input_user(self, message):
		self._input_message("user", message)

	def input_self(self, message):
		self._input_message("assistant", message)
	
	def _get_response(self):
		response = openai.ChatCompletion.create(
			model="gpt-3.5-turbo",
			messages=self.messages)

		return response["choices"][0]["message"]["content"]
	
	async def get_response(self):
		response = await self.loop.run_in_executor(ThreadPoolExecutor(), self._get_response)
		self.input_self(response)
		return response
		

