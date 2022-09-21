<h1>Chess Game project</h1>


<h2>want to play chess against your friends online or against the computer?</h2>
<h3>all you need to do is download the installer and run it!</h3>

<h4>how it works?</h4>
<p>
when playing against the computer it calculate the moves tree and combining same states to one node to form a graph<br>
it find same state using a hash table. each state has a uniqe code so when the cell is not empty we all ready caculated moves for this state.<br>
then, starting from nodes that are 4 moves away from it current state, each node return it perant which is the it best move<br>
ranking by the pawns stayed on the board. then each perant choose the opposite - it will return the child with the fewer points because we assume that the other <br>
will choose the best option for him. and it keep going until it return to the origin node.<br>
</p>


 <img src="https://eilon-projects-images.s3.eu-central-1.amazonaws.com/chess/chess+screen+shot.png" width="298" height="300"/>       
  
<img src="https://github.com/eilon1996/chess/blob/master/chess%20light.gif" width="498" height="280"/>
