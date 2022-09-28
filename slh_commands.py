from nextcord import Interaction
from nextcord.ext import commands

async def ticket_sys(interaction: Interaction, problem: str, bot: commands.Bot):
    channel = interaction.channel
    roles = interaction.user.roles
    guild = interaction.guild

    if "team" in channel.name:
        for role in roles:
            if "team" in role.name:
                await interaction.response.send_message(f"Your problem has been sent to the mentors")

                available_mentor = guild.get_role(1024553918795091998)
                claimed_mentor = guild.get_role(1024554391887413328)
                log_channel = guild.get_channel(1024415063655862442)
                claims = guild.get_channel(1024426110265589931)
                closed = guild.get_channel(1024576000157306972)

                ticket = await log_channel.send(f"{available_mentor.mention},help {role.mention} with: \n{problem}")

                def check_ticket(r, u):
                    return (str(r) == "🎟️" and u != bot.user and (available_mentor in u.roles))

                while True:
                    await ticket.add_reaction("🎟️")
                    _, assigned_mentor = await bot.wait_for("reaction_add", check=check_ticket)

                    await assigned_mentor.add_roles(role)
                    await assigned_mentor.add_roles(claimed_mentor)
                    await assigned_mentor.remove_roles(available_mentor)
                    await ticket.clear_reaction("🎟️")
                    await ticket.add_reaction("✅")
                    await ticket.add_reaction("❌")

                    def check_reaction(r, u):
                        return ((str(r) == "✅" or str(r) == "❌") and (u == assigned_mentor and u != bot.user))

                    def check_confirmation(r, u):
                        return((str(r) == "✅" or str(r) == "❌") and (role in u.roles) and (u != bot.user))

                    await interaction.channel.send(f"{assigned_mentor.name} has been assigned for your problem")

                    assignment = await claims.send(f"{assigned_mentor.name} has been assigned for {role.name}")

                    reaction, _ = await bot.wait_for("reaction_add", check=check_reaction)

                    await assigned_mentor.remove_roles(role)
                    await assigned_mentor.remove_roles(claimed_mentor)
                    await assigned_mentor.add_roles(available_mentor)
                    await ticket.clear_reaction("✅")
                    await ticket.clear_reaction("❌")

                    if str(reaction) == "✅":
                        confirmation = await interaction.channel.send(f"{role.mention}, your problem has been marked as solved!")

                        await confirmation.add_reaction("✅")
                        await confirmation.add_reaction("❌")

                        reaction, _ = await bot.wait_for("reaction_add", check=check_confirmation)
                        
                        await confirmation.clear_reaction("✅")
                        await confirmation.clear_reaction("❌")

                        if str(reaction) == "✅":
                            await ticket.delete()
                            await assignment.delete()
                            await closed.send(f"{assigned_mentor.name} solved {role.name}'s problem")
                            break
                        elif str(reaction) == "❌":
                            await interaction.channel.send(f"{role.mention}, your problem has been sent to be reassigned!")
                            ticket = await log_channel.send(f"{available_mentor.mention}, {role.mention}'s problem has been reopened: \n{problem}")
                            continue
                    elif str(reaction) == "❌":
                        await interaction.channel.send(f"{role.mention}, your problem has been sent to be reassigned!")
                        ticket = await log_channel.send(f"{available_mentor.mention}, {role.mention}'s problem has been reopened: \n{problem}")
                        continue

                break