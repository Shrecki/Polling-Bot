import os
from discord.ext import commands
from dotenv import load_dotenv
import core
import numpy as np
import datetime

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')


class CustomBot(commands.Bot):
    def __init__(self):
        """
        CustomClient constructor. Serves to initialize the command prefix.
        """
        self.cmd_prefix = '-'
        super(CustomBot, self).__init__(command_prefix=self.cmd_prefix)
        self.help_command = commands.DefaultHelpCommand(width=80000)
        self.add_command(self.start_poll)
        print(self.commands)

    async def on_ready(self):
        """
        Method called when the bot starts and connects to servers.
        For debug purposes, the bot displays the list of servers (so called guilds) to which it connects.
        :return:
        """

        print(f'{self.user} has connected to Discord!')

        for guild in self.guilds:
            print(
                f'{self.user} is connected to the following guild:\n'
                f'{guild.name}(id: {guild.id})'
            )

    async def display_unknown(self, message, args=None):
        await message.channel.send('Unknown command!')


    @staticmethod
    def filter_members_with_role_or_mention(ctx, members, roles, mentions):
        filteredMembers= []
        filteredMembers.extend(mentions)

        filteredRoleMembers = []
        if len(roles) != 0:
            for role in roles:
                roleMembers = list(filter(lambda member: role in member.roles, members))
                if len(roleMembers) != 0:
                    filteredRoleMembers.extend(roleMembers)

        filteredMembers.extend(filteredRoleMembers)
        filteredMembers = set(filteredMembers)
        return filteredMembers

    @commands.command(name='startpoll', help='polls every member of the channel for availability. Syntax is -startpoll '
                                             '@members_of_interest , where members_of_interest can be a group of users,'
                                             'an everyone tag or even several individual mentions, such as @member1 @member2 etc.'
                                             ' It is possible to mix any combination of the above, such as @group1 @member1.'
                                             ' It is also possible to specify the minimum duration '
                                             'of session to find (default is two hours). The syntax then becomes '
                                             '-startpoll @members_of_interest -t HH:MM. By default, the bot looks at '
                                             'calendars for one week, starting from the day the query is issued. It is'
                                             'possible to ask for more weeks, through the option -w n_weeks .'
                                             'Complete syntax is -startpoll @members_of_interest -t HH:MM -w n_weeks')
    async def start_poll(self, *, args=None):
        # This is the time for two hours in seconds
        minimum_length = 7200 * 1000

        # At minimum, bot will consider one week starting from today for availabilities.
        n_weeks = 1

        # Get all mentions and roles mentioned in the poll
        ctx = self
        mentions = ctx.message.mentions
        mentions_everyone = ctx.message.mention_everyone
        roles = ctx.message.role_mentions
        print(mentions)
        print(mentions_everyone)
        print(roles)

        # Check whether we had a time option specified and if so, retrieve its corresponding value
        full_query = ctx.message.content.split(' ')
        if '-t' in full_query:
            time_req = None
            if full_query.index('-t') < len(full_query) - 1:
                time_req = full_query[full_query.index('-t')+1]
                try:
                    minimum_length = core.convert_time_string_to_unix_timestamp(time_req)*1000
                except ValueError:
                    await self.send('Invalid format. Should conform to HH:MM, where HH and MM are both non negative.')
                    return
            else:
                await self.send('-t option expected an argument. Start over, idiot.')
                return

        if '-w' in full_query:
            weeks_req = None
            if full_query.index('-w') < len(full_query)-1:
                weeks_req = full_query[full_query.index('-w')+1]
                try:
                    weeks_req = int(weeks_req)
                except ValueError:
                    await self.send('Option -w expected an integer, but received {} instead. Try over.'.format(weeks_req))
                    return

                if weeks_req <= 0:
                    await self.send('Option -w expects a strictly positive integer, but received {}. Try over.'.format(weeks_req))
                    return
                else:
                    n_weeks = weeks_req
            else:
                await self.send('-w option expected an argument afterwards. Start over, idiot.')
        td = datetime.datetime.utcnow()
        from_optimistic, to_optimistic = core.get_from_and_to_optimistic(td, n_weeks=n_weeks)
        from_strict = core.get_from_strict(td)
        print('{} - {}'.format(from_strict, to_optimistic))

        await self.send('Poll started.')

        members_of_interest = []
        if mentions_everyone:
            for member in ctx.message.guild.members:
                members_of_interest.append(member)
        else:
            members_of_interest = CustomBot.filter_members_with_role_or_mention(ctx, ctx.message.guild.members,
                                                                                roles, mentions)

        overall_data = []
        missing_data_members = []
        for member in members_of_interest:
            member_data = core.convert_player_json(player_id=member.id, start_time=from_optimistic,
                                                   start_time_strict=from_strict,
                                                   end_time=to_optimistic)
            if member_data is None:
                missing_data_members.append(member)
            else:
                overall_data.append(member_data)

        intersections = core.find_intersections(overall_data, minimum_length=minimum_length)

        if len(intersections) == 0:
            msg= "Based on members availability, a game can't be scheduled in the next "+str(n_weeks) + " week"
            if n_weeks > 1:
                msg += 's'
            await self.send(msg)
        else:
            next_session = intersections[0]
            print('Next_session: {}'.format(next_session[0]))
            print('Next_session end: {}'.format(next_session[1]))
            interval = (next_session[1]-next_session[0])/1000
            days = np.floor(interval/(3600*24))
            hours = np.floor((interval-days*3600*24)/3600)
            minutes = np.floor((interval - days*3600*24 - hours * 3600)/60)

            time = core.convert_timestamp_to_date(next_session[0], french_time=True)
            time_rep = time.strftime('%H:%M')
            time_end = core.convert_timestamp_to_date(next_session[1], french_time=True).strftime('%H:%M')

            await self.send("Based on members availability, next session would be **" +
                            core.convert_number_to_day_string(time.weekday()) + " the " + str(time.day) + " of " +
                             core.convert_number_to_month_string(time.month) + " from " + time.strftime('%H:%M') + " to " + time_end + "**")

            for member in missing_data_members:
                await self.send("<@{}> did not fill availabilities.".format(member.id))


    @commands.command(name='help', help='shows help (duh)')
    async def display_help(self, args=None):
        """
        Help command. Displays help on how to use pauPoll, and what commands are available to users.
        """
        output = '`pauPoll bot is a polling bot destined to elect days where everyone in a group is available, ' \
                 'through totality voting. Its commands are of the form -command, where command is the relevant ' \
                 'command. Here are the available commands: \n'

        self.help_command.send_bot_help()


client = CustomBot()
client.run(TOKEN)
