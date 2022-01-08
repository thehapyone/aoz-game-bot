"""Responsible for different farming activities"""

class Farm:
    """
    The farming class.

    In order to be able to send troops to go farm,
    the below are thing things that needs to be sorted out:


     - Get max fleet size
     - Get current no of fleets used and available.
     - Ability to switch to outside city
     - Find and click on the radar button
     - Select a particular farming type
     - Increase and decrease the farming level
     - Get the current farming level
     - Click on the go to find the next available farm.
     - Detect the gather button and click on it to go gather.
     - Set out troops if any troops are available (atleast 10% of the max
     troops is needed to gather effectively)
     - Ability to find lower farm if current level not available.
     - Set out with the default formation
    """

    def __init__(self, farm_type: int):
        self._farm_type = farm_type

    def get_max_fleet(self):
        """
        Fetches and get the current game max fleet. It can
        also return the game current fleet as well if available.

        The max fleet size can be gotten from the garage under
        the troops management.
        :return: Int
        """
        '''
        # possible steps are below:
         - go to the city view
         - locate the garage
          - move mouse to the extreme left
          - find the garage target
        '''




