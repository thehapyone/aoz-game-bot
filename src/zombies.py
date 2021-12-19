"""Responsible for killing zombies in the Game event"""


class Zombies:
    """
    Zombies killing class.

    In order to be able to kill zombies in the game,
    some of this things need to be sorted out:
     - Get current mobility
     - Ability to switch to outside city screen
     - find and click on the green radar button
     - find and click on the find zombie radar
     - get the current level of zombie for the user
     - increase and decrease the zombie level.
     - click on go to find any available zombie
     - search and find the arrow that shows for about 6 secs before disappearing
     - click on the given zombie (confirm it is the right zombie level)
     - attack the zombie
     - set out with the default formation
     How do I know the zombie has been killed?
     - check the coordinate of the zombie and confirm the zombie is no more?
     - wait for period of time

    How do I know my attack troops have returned?
     - I can get the duration time to the target during 'set out' and
     multiple it by two to know the amount of time to wait for before
     restarting the attack again.
     - I check if the 'attack en route' or 'attack withdraw' is no more showing.

     - continue attacks as far mobility is greater than given limit.

    """

