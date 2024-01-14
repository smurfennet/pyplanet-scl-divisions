from pyplanet.apps.config import AppConfig
from pyplanet.contrib.command import Command

from pyplanet.apps.core.maniaplanet import callbacks as mp_signals
from pyplanet.apps.core.trackmania import callbacks as tm_signals


class SCLDivisionSupport(AppConfig):
	game_dependencies = ['trackmania']
	app_dependencies = ['core.maniaplanet', 'core.trackmania']
	mode_dependencies = []

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		self.is_warming_up = False

		self.setting_type = 'solo'
		self.setting_team_count = 4
		self.setting_player_count = 1

	async def on_start(self):
		self.context.signals.listen(mp_signals.map.map_start, self.map_start)
		self.context.signals.listen(mp_signals.flow.podium_start, self.podium_start)
		self.context.signals.listen(tm_signals.warmup_start, self.warmup_start)
		self.context.signals.listen(tm_signals.warmup_start_round, self.warmup_start)
		self.context.signals.listen(tm_signals.warmup_end, self.warmup_end)

		await self.instance.command_manager.register(
			Command(command='type', namespace='scl', target=self.chat_type, admin=False,
					description='Sets the competition type (solo or team).')
				.add_param(name='type', required=True, type=str),
			Command(command='teams', namespace='scl', target=self.chat_team_count, admin=False,
					description='Set the amount of teams.')
				.add_param(name='teams', required=True, type=int),
			Command(command='players', namespace='scl', target=self.chat_player_count, admin=False,
					description='Set the amount of players.')
				.add_param(name='players', required=True, type=int),
			Command(command='endround', namespace='scl', target=self.chat_end_round, admin=False),
		)

	async def map_start(self, restarted, map, **kwargs):
		# Reset mode settings & write information in the chat about the current settings.
		await self.set_server_settings()

	async def podium_start(self, *args, **kwargs):
		message = '$o$ff0Do not forget to make a screenshot and submit the results on the competition website!'
		await self.instance.chat(message)

	async def warmup_start(self, **kwargs):
		self.is_warming_up = True

	async def warmup_end(self, **kwargs):
		self.is_warming_up = False

	async def chat_type(self, player, data, **kwargs):
		# Change the current competition type (solo/team).
		if data.type is None or (data.type != 'solo' and data.type != 'team'):
			message = '$i$f00You have to provide a correct competition type (solo or team)!'
			await self.instance.chat(message, player)
			return

		self.setting_type = data.type
		await self.set_server_settings()

	async def chat_team_count(self, player, data, **kwargs):
		# Set the amount of teams.
		if data.teams is None or data.teams < 2 or data.teams > 8:
			message = '$i$f00You have to provide a correct amount of teams!'
			await self.instance.chat(message, player)
			return

		self.setting_team_count = data.teams
		await self.set_server_settings()

	async def chat_player_count(self, player, data, **kwargs):
		# Set the amount of players.
		if data.players is None or data.players < 1 or data.players > 8:
			message = '$i$f00You have to provide a correct amount of players!'
			await self.instance.chat(message, player)
			return

		self.setting_player_count = data.players
		await self.set_server_settings()

	async def chat_end_round(self, player, data, **kwargs):
		if self.is_warming_up:
			message = '$i$f00You cannot force the end of the warm-up round!'
			await self.instance.chat(message, player)
			return

		# Update the mode settings to up the amount of rounds per map.
		mode_settings = await self.instance.mode_manager.get_settings()
		mode_settings['S_RoundsPerMap'] = int(mode_settings['S_RoundsPerMap']) + 1
		await self.instance.mode_manager.update_settings(mode_settings)

		# End the round + inform players.
		await self.instance.gbx.multicall(
			self.instance.gbx('Trackmania.ForceEndRound', encode_json=False, response_id=False),
			self.instance.chat('$fff{}$z$s$ff0 ended the round and increased the amount of rounds to play to $fff{}$ff0.'.format(
				player.nickname,
				mode_settings['S_RoundsPerMap']
			))
		)

	async def set_server_settings(self):
		rounds_per_map = 10
		points_limit = 150 \
			if self.setting_type == 'team' \
			else 250
		points_repartition = await self.determine_team_points_repartition() \
			if self.setting_type == 'team' \
			else await self.determine_solo_points_repartition()

		# Update the mode settings.
		mode_settings = await self.instance.mode_manager.get_settings()
		mode_settings['S_FinishTimeout'] = 30
		mode_settings['S_AllowRespawn'] = True
		mode_settings['S_PointsLimit'] = points_limit
		mode_settings['S_RoundsPerMap'] = rounds_per_map
		mode_settings['S_ForceLapsNb'] = 1
		mode_settings['S_WarmUpDuration'] = -1
		mode_settings['S_WarmUpNb'] = 2
		mode_settings['S_UseAlternateRules'] = False
		mode_settings['S_UseTieBreak'] = False
		mode_settings['S_PointsRepartition'] = points_repartition
		await self.instance.mode_manager.update_settings(mode_settings)

		message = '$06fCurrent matchsettings: $fff{}$06f [{}players: $fff{}$06f]'.format(
			self.setting_type,
			'teams: $fff{}$06f, '.format(self.setting_team_count) if self.setting_type == 'team' else '',
			self.setting_player_count
		)
		await self.instance.chat(message)

	async def determine_team_points_repartition(self):
		repartition = ''

		if self.setting_team_count == 2:
			if self.setting_player_count == 1:
				repartition = '6, 3'
			elif self.setting_player_count == 2:
				repartition = '6, 4, 3, 1'
			elif self.setting_player_count == 3:
				repartition = '6, 5, 4, 3, 2, 1'
		elif self.setting_team_count == 3:
			if self.setting_player_count == 1:
				repartition = '9, 6, 3'
			elif self.setting_player_count == 2:
				repartition = '9, 7, 5, 3, 2, 1'
			elif self.setting_player_count == 3:
				repartition = '9, 8, 7, 6, 5, 4, 3, 2, 1'
		elif self.setting_team_count == 4:
			if self.setting_player_count == 1:
				repartition = '12, 9, 6, 3'
			elif self.setting_player_count == 2:
				repartition = '12, 10, 8, 6, 4, 3, 2, 1'
			elif self.setting_player_count == 3:
				repartition = '12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1'
		elif self.setting_team_count >= 5:
			if self.setting_player_count == 1:
				repartition = '15, 12, 9, 6, 3'
			elif self.setting_player_count == 2:
				repartition = '15, 13, 11, 9, 7, 5, 4, 3, 2, 1'
			elif self.setting_player_count == 3:
				repartition = '15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1'

		return repartition

	async def determine_solo_points_repartition(self):
		repartition = ''

		if self.setting_player_count == 2:
			repartition = '6, 3'
		elif self.setting_player_count == 3:
			repartition = '9, 6, 3'
		elif self.setting_player_count == 4:
			repartition = '12, 9, 6, 3'
		elif self.setting_player_count == 5:
			repartition = '15, 12, 9, 6, 3'
		elif self.setting_player_count == 6:
			repartition = '18, 15, 12, 9, 6, 3'
		elif self.setting_player_count == 7:
			repartition = '21, 18, 15, 12, 9, 6, 3'
		elif self.setting_player_count >= 8:
			repartition = '24, 21, 18, 15, 12, 9, 6, 3'

		return repartition

