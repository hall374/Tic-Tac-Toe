
from django.shortcuts import render_to_response
from django.http import HttpResponse
from django.template import RequestContext
import json
import random

# Class for holding ordered pairs
# Will make code in checkWin cleaner
class CenterWinOrderedPair:

	def __init__(self, x1, y1, x2, y2):
		self.x1 = x1
		self.y1 = y1
		self.x2 = x2
		self.y2 = y2

""" Static set of possible wins if the center was occupied
	by the last player that had a turn """
centerWins = [
	CenterWinOrderedPair(0,0,2,2),
	CenterWinOrderedPair(1,0,1,2),
	CenterWinOrderedPair(2,0,0,2),
	CenterWinOrderedPair(2,1,0,1)
]

# Check to see if the last player that took a turn won the game
def checkWin(request):
	if request.POST:
		# Parse the json from the request
		board = json.loads(request.POST['board'])
		lastSpaceTaken = json.loads(request.POST['lastSpaceTaken'])

		""" Check which player took the last turn by checking
			the character located on the board at the coordinates
			of lastSpactTaken """
		lastPlayer = board[lastSpaceTaken[0]][lastSpaceTaken[1]]

		win = False
		""" Keep track of the coordinates checked so if a winning set of
			coordinates is found, we can display the winning spot to the user """
		winningSpots = [];

		# Check if the last player that played occupied the board's center
		if board[1][1] == lastPlayer:
			""" Check each ordered pair to see if the last player occupies
				both spots in each pair (since he/she already has the center) """
			for pair in centerWins:
				x1 = pair.x1
				y1 = pair.y1
				x2 = pair.x2
				y2 = pair.y2
				if board[x1][y1] == lastPlayer and board[x2][y2] == lastPlayer:
					win = True
					# Add the center to winning spots
					winningSpots.append([1,1])
					winningSpots.append([x1, y1])
					winningSpots.append([x2, y2])
					break
		# If the player is not declared the winner, check any other win possibilities
		if not win:
			""" First, check if the player won horizonally accoring to the lastSpaceTaken
				If we count three occurrences of the same character, the last player won """
			lastPlayerCount = 0
			# Make our conditional statements in the loop shorter
			# lstX is "lastSpaceTaken x coordinate"
			lstX = lastSpaceTaken[0]
			lstY = lastSpaceTaken[1]
			winningSpots = []
			for i in range(0,3):
				""" Use mod in for (x+1)%3 because that will cover all horizontal coordinates
					even if the lastSpaceTaken is in the center (e.g. of the bottom row)"""
				if board[lstX][(lstY+i)%3] == lastPlayer:
					lastPlayerCount+=1
				winningSpots.append([lstX,i])
			if lastPlayerCount == 3:
				win = True
			else:
				""" If the player still hasn't won, check if he/she won vertically using the
					same logic as above """
				lastPlayerCount = 0
				winningSpots = []
				for j in range(0,3):
					if board[(lstX+j)%3][lstY] == lastPlayer:
						lastPlayerCount+=1
					winningSpots.append([j,lstY])
				if lastPlayerCount == 3:
					win = True
		# Convert our variables into JSON and respond to the AJAX request
		results = {
			'win': win,
			'winningSpots': winningSpots
		}
		json_results = json.dumps(results)
		return HttpResponse(json_results, mimetype="application/json")

# Process the current game board and return the best possible solution
def AI_turn(request):
	if request.POST:
		# Parse the json from the request
		board = json.loads(request.POST['board'])
		lastSpaceTaken = json.loads(request.POST['lastSpaceTaken'])

		# Coordinates of the spot the AI chooses
		chosenCoords  = None

		# First, check if AI can win on this move
		
		# If the AI already owns the center
		if board[1][1] == 'x':
			for pair in centerWins:
				x1 = pair.x1
				y1 = pair.y1
				x2 = pair.x2
				y2 = pair.y2
				if board[x1][y1] == 'x' or board[x2][y2] == 'x':
					""" This means the AI has a winning move using the center
						if no 'o' is present in the diagonal """
					if board[x1][y1] == 'x' and not board[x2][y2]:
						chosenCoords = [x2, y2]
						break
					elif not board[x1][y1]:
						chosenCoords = [x1, y1]
						break		
		if not chosenCoords:	
			# If the AI cannot win using the center, check each row				
			for i in range(0, 3):					
				# If there is more than 1 x in a row, the AI has a winning move					
				if board[i].count('x') > 1 and board[i].count('o') == 0:						
					""" If there's more than one x and no o is found in the row,							
						then there is one and only one empty spot in the row, at							
						which the value is None """						
					try:
						chosenCoords = [i, board[i].index(None)]
						break
					except ValueError:
						pass

			if not chosenCoords:
				for j in range(0, 3):
					columnList = []
					for k in range(0, 3):
						columnList.append(board[k][j])
					# Same logic as when checking the rows
					if columnList.count('x') > 1 and columnList.count('o') == 0:
						try:
							chosenCoords = [columnList.index(None),j]
							break
						except ValueError:
							pass
        
		# If the AI cannot win, try to find the spot to keep from losing
		if not chosenCoords:
			# First, check if the center has been taken...if not, take the center!
			if not board[1][1] and board[1][1] != 'o':
				chosenCoords = [1,1]
			else:
				""" First, the AI must do the opposite of what it did earlier in checking
					if it could win using the center
					Now check if o can win using the center and block accordingly """
				if board[1][1] == 'o':
					for pair in centerWins:
						x1 = pair.x1
						y1 = pair.y1
						x2 = pair.x2
						y2 = pair.y2
						if board[x1][y1] == 'o' or board[x2][y2] == 'o':
							""" This means the AI must block the player from winning
								using the center if it hasn't already done so """
							if board[x1][y1] == 'o' and not board[x2][y2]:
								chosenCoords = [x2, y2]
								break
							elif not board[x1][y1]:
								chosenCoords = [x1, y1]
								break		
				if not chosenCoords:						
					""" If the AI still hasn't found a solution, check if the human has two in a row in 
						relation to the last chosen spot """
					""" Make our conditional statements in the loop shorter
						lstX is "lastSpaceTaken x coordinate" """
					lstX = lastSpaceTaken[0]
					lstY = lastSpaceTaken[1]

					# Check the row in which the last spot was taken
					if board[lstX].count('o') > 1 and board[lstX].count('x') == 0:
						try:
							chosenCoords = [lstX,board[lstX].index(None)]
						except ValueError:
							pass

					""" If a solution still hasn't been found, check the column in which 
						the last spot was taken """
					columnList = []
					if not chosenCoords: 
						for l in range(0, 3):
							columnList.append(board[l][lstY])
						# If o can win if there's a blank spot, take the blank spot
						if columnList.count('o') > 1 and columnList.count('x') == 0:
							try:
								chosenCoords = [columnList.index(None), lstY]
							except ValueError:
								pass

					""" If the AI could not win or block, the user can still use one
						or more solutions that provide him or her multiple winning 
						moves
						These next statements are for preventing those solutions """
					if not chosenCoords:
						""" Coordinates for corner spaces and corresponding coordinates
							for opposite corners by list index
							e.g. corners[0] is opposite corner of cornerOpposites[0] """
						corners = [
							[0,0],
							[0,2],
							[2,0],
							[2,2]
						]
						cornerOpposites = [
							[2,2],
							[2,0],
							[0,2],
							[0,0],
						]
						# Horizontal sides
						horizSides = [
							[1,0],
							[1,2]
						]
						# Vertical sides
						verticalSides = [
							[0,1],
							[2,1]
						]

						MAX_LOOPS = 20
						if lastSpaceTaken in corners:
							""" If the user chooses two opposite corners and the user cannot be 
							blocked from a winning move, or the AI cannot make a winning move,
							then the AI can choose any side and prevent defeat """
							oppositeCorner = cornerOpposites[corners.index(lastSpaceTaken)]
							if board[oppositeCorner[0]][oppositeCorner[1]] == 'o':
								""" Two opposite corners are filled
									Choose any side to occupy to prevent defeat by this soultion 
									Choose it randomly to help prevent predictability """
								numLoops = 0
								while not chosenCoords and numLoops < MAX_LOOPS:
									numLoops += 1
									sides = horizSides+verticalSides
									randSideIndex = random.randint(0, len(sides)-1)
									chosenSide = sides[randSideIndex]
									if not board[chosenSide[0]][chosenSide[1]]: 
										chosenCoords = sides[randSideIndex]
							elif not board[oppositeCorner[0]][oppositeCorner[1]]:
								chosenCoords = oppositeCorner
						elif lastSpaceTaken in (horizSides+verticalSides):
							""" If the last space taken is a side, check if the two
							adjacent corners for occupation. If they're both unoccupied,
							occupy one of them. 
							This is the solution to when the user takes a middle side and
							a corner opposite to that side """
							
							""" Need to know if it is a vertical or horizontal side
								Get adjacent corners to a horizontal side with x+-1
								Get adjacent corners to vertical side with y+-1 								Get a random index to make the AI less predictable
								Choosing either adjacent corner will prevent defeat"""
							cornerToChooseSwitch = random.randint(0, len(horizSides)-1)
							if lastSpaceTaken in horizSides:
								if((board[lstX+1][lstY] is None) and (board[lstX-1][lstY] is None)):
									if cornerToChooseSwitch > 0:
										chosenCoords = [lstX+1,lstY]
									else:
										chosenCoords = [lstX-1, lstY]
							elif lastSpaceTaken in verticalSides:
								if((board[lstX][lstY+1] is None) and (board[lstX][lstY-1] is None)):
									if cornerToChooseSwitch > 0:
										chosenCoords = [lstX,lstY+1]
									else:
										chosenCoords = [lstX, lstY-1]
						elif not chosenCoords:							
							# Loop until a corner that hasn't been taken is chosen
							# Stop at to prevent infinite loop at last move
							numLoops = 0
							while not chosenCoords and numLoops < MAX_LOOPS:
								numLoops += 1
								randCornerIndex = random.randint(0, len(corners)-1)
								chosenCorner = corners[randCornerIndex]
								if not board[chosenCorner[0]][chosenCorner[1]]: 
									chosenCoords = corners[randCornerIndex]

					""" If every other condition has passed and there's still no
						solution, find a free spot and take it.
						This should only happen during a stalemate scenario
						when the AI has the last move"""
					if not chosenCoords:
						for idx, lst in enumerate(board):

							try:
								if board[idx].index(None) >= 0:
									chosenCoords = [idx, board[idx].index(None)]
									break;
							# list.index throws a value error if the item is not found
							except ValueError:
								pass



		# Convert our variables into JSON and respond to the AJAX request
		results = {
			'chosenCoords': chosenCoords,
		}
		json_results = json.dumps(results)
		return HttpResponse(json_results, mimetype="application/json")				