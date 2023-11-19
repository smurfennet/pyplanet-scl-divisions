# pyplanet-scl-divisions
PyPlanet app for managing divisions for the Smurfen.net Canyon League competitions.
The app provides commands to set-up the correct match settings based on the competition type, amount of teams (optional), and the amount of players in the submatch.

**All commands in this plugin can be used by everyone on the server. Ensure proper access control for the server you're driving on.** 

## Normal use
* Set the competition type: `/scl type (solo|team)`
  * For a solo match: `/scl type solo`
  * For a team match: `/scl type team`
* [Team] Set the amount of teams in the match: `/scl teams (number of teams)`
  * For example: `/scl teams 4`
* Set the amount of players in the match `/scl players (number of players)`
  * [Solo] Provide the total amount of players
  * [Team] Provide the amount of players per team

## Extra commands
### End current round
* `/scl endround`
* Will end the current round and add another round to play on this map.
