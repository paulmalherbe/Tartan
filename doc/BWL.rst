Bowls Clubs
-----------
Tabs (BC)
.........
Control Record (BC)
+++++++++++++++++++
Use this routine to create the bowls control record.

+ **M/L Integration** - Select whether or not the bowls system is integrated with the Member's system, if applicable.
+ **Same Numbers** - If integrated with the member's system is the tab number the same as the member number, if applicable.
+ **Male Start Seq** - The number range for male bowler's tab numbers.
+ **Female Start Seq** - The number range for female bowler's tab numbers.
+ **Non-member Start Seq** - The number range for non-member's player codes. This number must be greater than the male and female numbers.
+ **Draw Base** - By pre-allocated Position, Rating or a Combination of both.
+ **Rating Order** - Whether the rating system is ascending or descending, like golf handicaps.
+ **Mixed Ratings** - Whether to use different ratings for mixed gender draws.
+ **Default Team Size** - When doing a tabs-in draw use this as the default team size.
+ **Replace Fours** - When doing a trips tabs-in draw use pairs instead of fours for eight players.
+ **Weeks Between Draws** - The minimum number of weeks that team members should not be in the same team again. They could however be drawn to play against them.
+ **Rate - Member** - The member's rate.
+ **Rate - Visitor** - The visitor's rate.
+ **Greens** - The available green codes e.g. AB
+ **Draw Format** - The format to print the draw sheets as follows:
    + **S32L-S32L** - Skip, 3rd, 2nd, Lead - Skip, 3rd, 2nd, Lead
    + **S32L-L23S** - Skip, 3rd, 2nd, Lead - Lead, 2nd, 3rd, Skip
+ **Email Address** - The email address of the person in charge of bowls, if not the default email address in the company record.

Tab's Maintenance (BC)
++++++++++++++++++++++
Use this routine to create, delete or amend tab records.

+ **Tab Number** - The number of the tab or zero for the next available number depending on the gender of the member.
+ **Membership Number** - If the Member system is integrated and, the numbers are not the same, enter the member's membership number and the details will be obtained from there.
+ **Surname** - The person's surname.
+ **Names** - The person's names.
+ **Gender** - The person's gender.
+ **Address Line 1** - The person's address line 1.
+ **Address Line 2** - The person's address line 2.
+ **Address Line 3** - The person's address line 3.
+ **Postal Code** - The person's postal code.
+ **Home Number** - The person's home phone number.
+ **Work Number** - The person's work phone number.
+ **Cell Number** - The person's mobile phone number.
+ **Email Address** - The person's email address.
+ **Position - Primary** - The position the person should normally play.
+ **Rating - Primary** - The person's rating as graded by the selectors.
+ **Position - Mixed** - The position the person should play in mixed bowls.
+ **Rating - Mixed** - The person's rating in mixed bowls.
+ **Association Number** - The person's number with the bowling association.

|

In addition there are the following buttons.

+ **Import** - Use this button to import, only tab ratings for existing tabs or all tab details for existing and new members, from an excel (xls) or comma separated (csv) file.
+ **Accept** - Use this button to accept the current details as shown.
+ **Convert** - Use this button to convert visitor's tabs to member's tabs.
+ **Print** - Use this button to print a listing of member's details.

Tabs-In Draw (BC)
+++++++++++++++++
Use this routine to make a new draw or to amend a current draw.

+ **Date** - The date of the draw.
+ **Time** - The time of the draw. If a draw with the same date and time already exists the following options will be available:
    + **None** - Do nothing, return to the time entry.
    + **View** - View the existing draw.
    + **Reprint** - Reprint the existing draw.
    + **Alter** - Alter the existing draw.
    + **Clear** - Clear, delete, the existing draw.
+ **Mixed Gender** - Whether or not the draw is mixed.
+ **Mixed Rating** - Whether or not to use the alternative ratings.
+ **Draw By** - If available select whether to base the draw on Positions, Ratings or a Combination of both.
+ **Fees - Member** - The fee charged per member.
+ **Fees - Visitor** - The fee charged per visitor.

|

Once the above fields have been entered capture all tabs as follows:

+ **Tab Number** - The player's tab number. Enter zero for a visitor. A number will be allocated to the visitor which can then be written on his tab e.g. 901.
+ **Surname** - The player's surname. Only for visitors.
+ **Names** - The player's names. Only for visitors.
+ **Gender** - The player's gender. Only for visitors.
+ **Position** - The player's position. Only for visitors.
+ **Rating** - The player's rating. Only for visitors.
+ **Paid** - Whether or not the player has paid.

|

The following *Buttons* are available:

+ **Bounce** - Use this button to enter bounce games.
+ **Teams** - Use this button to enter arranged teams.
    + **Team Size** - Enter the required team size.
    + **Prefer Pairs** - Whether or not to replace fours with pairs. This only applies when the team size is three.
+ **Entered** - Use this button to display all entered players.
+ **Modify** - Use this button to change the player's position/ratings for this draw only.
+ **Draw** - Use this button to make the draw once all tabs/teams and bounce games have been entered. In the case of *Teams* if there are any tabs that have been entered and have not been allocated to teams you will be prompted to either *Generate*, *Delete* or *Exit*. If *Generate* is selected the program will try to allocate the unallocated tabs into teams.
    + **Draw Type** - The type of draw i.e. Random or Strength v Strength.
    + **Apply Percentages** - This is only available if the basis of the draw is Combined. Select whether to apply percentages to position changes e.g. A player moving up in position would lose 10% of their rating and a player moving down in position would gain 10% of their rating.
    + **Apply History** - Whether or not to take previous draws into consideration when making the current draw.
    + **Team Size** - The preferred number of players per team.
    + **Prefer Pairs** - Whether or not to replace fours with pairs. This only applies when the team size is three.
    + **Greens** - The greens to be used. This is in the format A,B or A,B234 showing green code and rinks. If the rinks are not entered they will default to 6. If 7 rinks are available this must be entered as A1234567,B etc. If there are more rinks available than needed, end rinks will be removed.
+ **View/Edit Draw** - Use this button to view the draw and/or manually change it i.e. move players between teams or replace players with new players.
+ **Print** - Use this button to print a draw.
    + **Print Cards** - Select whether to print score cards.
        + **Heading** - Enter the heading to be printed on the score cards.
        + **Number of Ends** - Enter the number of ends being played.
    + **Cash Takings Sheet** - Print a cash takings sheet.
    + **Tabs Draw Listing** - Print a tabs draw list in tab number.
    + **Tabs Draw Board** - Print an emulation of a tabs draw board.
    + **Include Empty Rinks** - Whether to include or exclude empty rinks when printing a tabs draw board.
+ **Exit** - Use this button to exit the program. If the draw has not yet been done you will be prompted to confirm exiting.

View/Edit Draw (BC)
+++++++++++++++++++
Use this routine to view and/or alter a draw manually.

Use the *Replace Tab with New Tab* button to replace a player with another player not yet in the draw. This will remove the old player in insert the new player.

Reprint Draw (BC)
+++++++++++++++++
Use this routine to reprint a previous draw.

+ **Date** - The date of the draw.
+ **Time** - The time of the draw.
+ **Cash Takings Sheet** - Print a cash takings sheet.
+ **Tabs Draw Listing** - Print a tabs draw list in tab number.
+ **Tabs Draw Board** - Print an emulation of a tabs draw board.
+ **Include Empty Rinks** - Whether to include or exclude empty rinks when printing a tabs draw board.

How the Draw Works (BC)
+++++++++++++++++++++++
All the tab numbers, names and ratings are stored in a relational database.

When a draw is made the following takes place:

+ **Required Positions** - Based on the number of entered players and the selected team size i.e. 1, 2, 3 or 4, we now calculate the number of skips, thirds, seconds and leads required. This takes split rinks into consideration as well.
+ **Ratings Only** - If only ratings are being used, i.e. no positions, the required number of players by position will be allocated by strength i.e. the required number of skips will be the highest rated players and the required number of thirds the next highest rated etc.
+ **Positions Only** - If only positions are being used, i.e. no ratings, and the required number of players, by position, is short the additional players will be randomly selected from the lower positions, in order.
+ **Combination** - If a combination of positions and ratings is used and the required number of players, by position, is short the additional players will be the highest rated from the lower positions, in order. If `Apply Percentages` has been selected, all players elevated to a higher position lose 10% of their rating, by position, for the current draw e.g. a third rated 18 could become a skip rated 16 or a second rated 20 could become a skip rated 16. The reverse also applies i.e. players can gain 10%, by position, if demoted to a lower position.
+ **Draw**
    + **Random** - 5,000 `RANDOM` draws are now generated and the one with the least number of anomalies is selected.
        + **Teams** - Teams are created by randomly selecting a skip, third, second and lead. This is repeated until all players have been placed.
        + **Anomalies**
            + **When applying history** - If `Apply History` was selected the history period is the period entered on the bowls control record under `Weeks Between Draws` e.g. 4 weeks which equals 28 days.
                + *Skips that have played against each other during the history period*
                + *Players that have played with the same players during the history period*
                + *Players that have played in a broken rink during the history period*
            + **Always**
                + *Difference in team strengths*
    + **Strength v Strength** - A single draw is generated as follows:
        + **Teams** - Teams are created by placing the highest rated skip with the highest rated third with the highest rated second with the highest rated lead. This is repeated until all players have been placed.
        + **Balance** - Teams are then paired and balanced i.e. players might be moved from one team to another to try and equalise the team strengths.

Tabs 321 Draw (BC)
++++++++++++++++++
Use this routine to make a new 321 draw.

+ **Date** - The date of the draw.
+ **Time** - The time of the draw. If a draw with the same date and time already exists some of the following options will be available:
    + **None** - Do nothing, return to the time entry.
    + **View** - View the existing draw.
    + **Reprint** - Reprint the existing draw.
    + **Alter** - Alter the existing draw.
    + **Delete** - Delete, the existing draw.
+ **Fees - Member** - The fee charged per member.
+ **Fees - Visitor** - The fee charged per visitor.

|

Once the above fields have been entered capture all tabs as follows:

+ **Tab Number** - The player's tab number. Enter zero for a visitor. A number will be allocated to the visitor which can then be written on his tab e.g. 901.
+ **Surname** - The player's surname. Only for visitors.
+ **Names** - The player's names. Only for visitors.
+ **Paid** - Whether or not the player has paid.

|

The following *Buttons* are available:

+ **Entered** - Use this button to display all entered players.
+ **Do Draw** - Use this button to make the draw once all tabs/teams and bounce games have been entered. In the case of *Teams* if there are any tabs that have been entered and have not been allocated to teams you will be prompted to either *Generate*, *Delete* or *Exit*. If *Generate* is selected the program will try to allocate the unallocated tabs into teams.
    + **Draw Type** - The type of draw i.e. Random or Strength v Strength.
    + **Apply History** - Whether or not to take previous draws into consideration when making the current draw.
    + **Competitors** - The preferred number of players per game.
    + **Greens** - The greens to be used. This is in the format A,B or A,B234 showing green code and rinks. If the rinks are not entered they will default to 6. If 7 rinks are available this must be entered as A1234567,B etc. If there are more rinks available than needed, end rinks will be removed.
+ **View** - Use this button to view the draw and/or manually change it i.e. move players between teams or replace players with new players.
+ **Print** - Use this button to print a draw.
    + **Cash Takings Sheet** - Print a cash takings sheet.
+ **Exit** - Use this button to exit the program. If the draw has not yet been done you will be prompted to confirm exiting.

League (BC)
...........
Club Records (BC)
+++++++++++++++++
Use this routine to add, amend and delete club records. These records are used by the `League Selections` modules.

+ **Club Code** - The applicable club's code. A zero code will automatically select the next available code.
+ **Club Name** - The name of the club.

League Formats (BC)
+++++++++++++++++++
Use this routine to create league format records e.g. Flag or Muter.

+ **Format Code** - The applicable format code. A zero code will automatically select the next available code.
+ **Description** - The description of the format.
+ **Assessment Forms** - Allow printing of assessment forms.
+ **Number of Forms** - Print assessment form per team or individual.
+ **Assess Self** - Whether the player must assess himself.
+ **Rating Out Of** - What the maximum assessment rating could be.
+ **Sets Format** - Whether sets are to be played.
+ **Logo** - The logo image file of the sponsor, if applicable.

Side's Maintenance (BC)
+++++++++++++++++++++++
Use this routine to create or amend side records. These are sides as entered in the league e.g. `WPCC A` or `WPCC B`.

+ **Format Code** - The applicable league format code as created using `League Formats (BC)`_.
+ **Side Code** - The applicable side code. A zero code will automatically select the next available code.
+ **Description** - The description of the side e.g. `WPCC A`
+ **League** - Select whether this side is playing in the `Main` or `Friendly` league.
+ **Division** - The division that the side is playing in e.g. `PR`, `1A` etc.
+ **Number of Teams** - The number of teams in the side.
+ **Active Flag** - Whether or not this side is still active. If a team gets relegated or promoted it must be made inactive and a new side must be created. An inactive side can be made active again in the future if it once again becomes applicable.

Capture Selections (BC)
+++++++++++++++++++++++
Use this routine to capture team selections as follows:

+ **Format Code** - The applicable league format code as created using `League Formats (BC)`_.
+ **Type** - Select the type of match, Fixture or Practice.
+ **Match Date** - YYYYMMDD.
+ **Side Code** - The applicable side code. If no sides have as yet been entered enter a zero and create a side code as follows:
    + **Side Description** - The description on the side.
    + **League (M/F)** - Main or Friendly league.
    + **Side Division** - The division of the side. PR for the premier side and 1A, 1B, 2A etc
    + **Number of Teams** - The number of teams in the side.
+ **Opposition Code** - The applicable opposition side code. If the opponent's record has not yet been captured enter a zero and create the opposition's side code as follows:
    + **Club Code** - Enter an existing club code or zero for a new club.
    + **Club Name** - Enter the club's name if it is a new club.
    + **Side Name** - Enter the opposition side's name e.g. WPCC A or WPCC B
+ **Venue (H/A/Name)** - Enter where the match is being played, at (H)ome, (A)way or another location.
+ **Meeting Time** - Enter the time the side must meet on the day of the match.
+ **At (H/A/Name)** - Enter where the side must meet, at (H)ome, (A)way or another location.
+ **Captain Code** - The tab code of the captain.
+ **Enter the teams as follows**:
    + **Skp** - The tab code of the skip.
    + **Plr** - The tab code of the next team member.
+ When all sides have been entered press the `Esc` key twice to exit. You will then be asked whether or not you would like to View or Print the Selections. If Yes continue as follows:

Assessment Forms (BC)
+++++++++++++++++++++
Use this routine to print assessment forms as follows:

+ **Format Code** - The applicable league format code.
+ **Type** - Select the type of match, Fixture or Practice.
+ **Match Date** - Enter the match date to print.

Declaration Forms (BC)
++++++++++++++++++++++
Use this routine to print declaration forms as follows:

+ **Format Code** - The applicable league format code.
+ **Match Date** - Enter the match date to print.

Capture Assessments (BC)
++++++++++++++++++++++++
Use this routine to capture completed assessment forms as follows:

+ **Format Code** - The applicable league format code.
+ **Type** - Select the type of match, Fixture or Practice.
+ **Match Date** -  Enter the match date to capture.
+ **Number of Forms** - The number of forms per team.
+ For each completed form enter the following.
    + **Skp** - The skip's tab code.
    + **Plr** - If capturing 4 forms per team enter the player's tab code.
    + **SF** - The number of shots the team scored.
    + **SA** - The number of shots the opposition scored.
    + **4** - The skip's rating.
    + **3** - The third's rating.
    + **2** - The second's rating.
    + **1** - The lead's rating.
    + **Remarks** - Any remarks.

Match Assessment Report (BC)
++++++++++++++++++++++++++++
Use this routine to print a match assessment report as follows:

+ **Format Code** - The applicable league format code.
+ **Type** - Select the type of match, Fixture or Practice.
+ **Match Date** - Enter the match date to print.

Assessment Summary (BC)
+++++++++++++++++++++++
Use this routine to print an assessment summary as follows:

+ **Format Code** - The applicable league format code.
+ **Type** - Select the type of match, Fixture or Practice.
+ **First Round Date** - Enter the date that the first round of the season was played.

Club Competitions (BC)
......................
Competition Types (BC)
++++++++++++++++++++++
Use this routine to create competition type records as follows:

+ **Type Code** - zero for the next number else an existing number. To see existing types press the F1 key.
+ **Description** - The competition description.
+ **Competition Format** - The type of competition i.e. Tournament, K/Out (D), K/Out (N), R/Robin or Teams. K/Out (D) is for drawn teams knockout and K/Out (N) is for nominated teams knockout. Teams is for a competition between the home club and a visiting club.
+ **Team Size** - The number of players in a team.
+ **Number of Games** - The total number of games comprising the competition.
+ **Number of Ends per Game** - The number of ends to be completed in a game.
+ **Groups by Position** - Whether or not the teams must be split into different groups. If grouping is not going to occur continue with `Strict S v S` below.
+ **Group After Game** - Select the game after which the grouping is to take place.
+ **Adjust Scores** - Whether or not the scores are to be adjusted.
+ **Expunge Games** - Which games, if any, must be expunged i.e. cleared. The games must be comma separated e.g. 1,2
+ **Retain Percentage** - What percentage of the shots of the games, not expunged, must be retained when split into groups.
+ **Number of Drawn Games** - The number of games which are randomly drawn. Enter 99 for a Round Robin.
+ **Strict S v S** - Whether the competition is strictly strength versus strength i.e. teams could play each other again before the last game.
+ **Different Drawn Games Scoring** - Whether or not drawn games have a different scoring format from strength versus strength games.
+ **Points Format** - The formats for Drawn and Strength V Strength games.
    + **Skins** - Whether or not to have skins.
    + **Number of Ends per Skin** - If skins were selected then enter the number of games per skin.
    + **Points Only** - Only points are to be captured i.e. no shots.
    + **Points per End** - Number of points per end won.
    + **Points per Skin** - If skins were selected then enter the number of points allocated per skin.
    + **Points per Game** - Number of points for the game.
    + **Bonus Points** - Whether to allocated a bonus point.
    + **Win by More Than** - If bonus points are allocated enter the number of points which the winning margin must be more than.
    + **Lose by Less Than** - If bonus points are allocated enter the number of points which the losing margin must be less than.

Capture Entries (BC)
++++++++++++++++++++
Use this routine to capture entries in a competition as follows:

+ **Code** - The relevant competition number or zero for the next available number.
+ **Name** - The name of the competition.
+ **Date** - The starting date of the competition.
+ **Type** - The competition type as created in `Competition Types (BC)`_. To create a new type enter 0 and hit Enter.

In the event of drawn games enter all player's codes else enter only the skip's codes.

+ **Code** - The player's code as created in `Tab's Maintenance (BC)`_ or you can enter a zero to enter a new player as per `Tab's Maintenance (BC)`_.
+ **Team** - The team's code, if relevant i.e. H or V if the competition type is Teams.
+ **P** - Whether or not the player has paid, Y or N.

Entries Listing (BC)
++++++++++++++++++++
Use this routine to print a list of entered players.

+ **Competition Code** - The relevant competition number.

Competition Format (BC)
+++++++++++++++++++++++
Use this routine to print the competition format.

+ **Competition Code** - The relevant competition number.
+ **Notes** - The notes relevant to this competition e.g. No trial ends. Please note that termination of this field is the <F9> key and and not <Return> or <Enter> key.

Competition Draw (BC)
+++++++++++++++++++++
Use this routine to create a draw and, if relevant, print match cards as follows:

+ **Tournament, Teams and Round Robin**
    + **Competition Code** - The relevant competition code. If the competition is a new competition and is a Round Robin competition you will have the facility to sectionalise it.
        + **Sections** - Select Yes or No.
        + **Entries per Section** - Enter the number of entries per section.
    + **Game Number** - The relevant game number.
    + **Game Date** - The date of the game.
    + **Pair Home with Away Skips** - This only applies to the first drawn game.
        + **No** - Standard random draw where anyone could be paired with anyone.
        + **Yes** - An attempt will be made to pair visitors with local members.
    + **Number of Groups** - The number of groups, if applicable, to split the players into.
    + **Smallest Group** - Select which group will have the least number of teams, if applicable.
    + **Greens** - The greens to be used, comma separated e.g. A,B,C will default to 6 rinks per green. You can default a green to seven by entering A7,B7,C which would give us 20 rinks. You can also exclude rinks by entering rinks to be used e.g. A2345,B345 which would give us 7 rinks.
    + **Group per Green** - Whether to allocate greens to groups. This only applies to the final game.
    + **Print Cards** - Whether or not to print score cards.
    + **Card Type** - If available, select the type of scorecard to print.
        + **Ends** - A scorecard showing all ends.
        + **Totals** - A scorecard showing only game totals.
    + **All Cards** - If cards were selected to be printed, whether to print all cards or only selected ones.

+ **Knockout**
    + **Competition Code** - The relevant competition code.
    + **Completion Dates** - Enter the dates each round must be completed by.
    + **Number of Seeds** - Enter the number of seeded players and then enter each seeded player's code, in sequence, starting with the first seed.

Draw Summary (BC)
+++++++++++++++++
Use this routine to print a summary of all draws, excluding knockout, to date.

+ **Competition Code** - The relevant competition number.

Change Draw (BC)
++++++++++++++++
Use this routine to change individual draws, excluding knockout, in a competition. After changing the draws you must reprint them as per `Competition Draw (BC)`_. Please note that to only reprint certain cards you must select `All Cards No`.

+ **Competition Code** - The relevant competition code.
+ **Game Number** - The relevant game number.
+ **Greens** - The available greens comma separated e.g. A,B,C
    + **S-Code** - The skip's code.
    + **O-Code** - The opposition's code.
    + **RK** - The rink number e.g. A1

Capture Game Results (BC)
+++++++++++++++++++++++++
Use this routine to capture completed games, excluding knockout, as follows:

+ **Competition Code** - The relevant competition code.
+ **Game Number** - The relevant game number.
    + **Drawn** - If the next game has already been drawn you will have the ability to expunge the draw and change the results already captured.
+ **Ends Completed** - The number of ends completed. Enter a zero to abandon a game.
    + **S-Code** - The skip's code.
    + **SF** - Shots scored by the skip's side.
    + **Pnts** - Points scored by the skip's side.
    + **O-Code** - The opposition's code.
    + **SA** - Shots scored by the opposing side.
    + **Pnts** - Points scored by the opposing side.

Match Results Report (BC)
+++++++++++++++++++++++++
Use this routine to print the match results as follows:

+ **Competition Code** - The relevant competition code.
+ **Last Game** - The last game to take into account.
+ **Game Report** - Print the last game's results.

If the last game of the competition is being printed, enter the following:
    + **Session Prizes** - Whether session prizes are to be awarded.
    + **Session Prizes by Group** - Whether session prizes are to be awarded by group.

    Prizes by Group or the Match if not Grouped

    + **Number Prizes** - The number of prizes being awarded.
    + **EFT Forms** - Whether to print EFT Forms in which case you will be required to enter the total value of each prize.

Results are ranked in the order of most points, largest shot difference and then least shots conceded.

If the competition type is a Sectional Round Robin you will be asked whether you want to generate and print a Play-Off draw. Should you decide not to do so at this stage you can do so at another time by reprinting this report.

Contact Request Forms (BC)
++++++++++++++++++++++++++
Use this routine to print forms with player's missing contact details.

Toolbox (BC)
............
Change Tab Numbers (BC)
+++++++++++++++++++++++
Use this routine to change Tab numbers.

+ **Old Tab** - The old tab number
+ **New Tab** - The new tab number

The **Generate** button is used to automatically renumber tabs in surname and names sequence.

Delete Visitors' Tabs (BC)
++++++++++++++++++++++++++
Use this routine to delete visitor's tabs without competition history and re-number the remaining visitor's tabs.

+ **Minimum Tabs-In** - Enter the minimum number of times a visitor must have played tabs-in to stay in the system.

Competition Envelopes (BC)
++++++++++++++++++++++++++
Use this routine to print envelopes for competition prizes.

+ **Competition Code** - The relevant competition code.
+ **Groups** - The number of groups, if applicable.
+ **Prizes** - The number of prizes per group.
+ **Members** - The number of players per team.

Clear History (BC)
++++++++++++++++++
Use this routine to selectively erase historical data. Please ensure that you make a **backup** before selecting this routine as there is no going back.

+ **Tabs-Inn** - Delete all history relating to tabs-inn draws.
+ **League** - Delete all history relating to league selections.
+ **Competition Entries** - Select which competition entries to delete.
+ **Competition Type** - If all entries of a type are deleted must the type also be deleted.
