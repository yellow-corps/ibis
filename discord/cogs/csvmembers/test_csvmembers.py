from unittest import mock
from redbot.core import commands
import pytest
import discord
from .csvmembers import CsvMembersBuilder, CsvMembersCog


@pytest.mark.asyncio
async def test_command_success():
    builder = mock.Mock(CsvMembersBuilder)
    builder_cls = mock.Mock(return_value=builder)
    cog = CsvMembersCog(builder_cls=builder_cls)

    builder_cls.assert_called_once_with()
    assert cog.builder == builder

    ctx = mock.AsyncMock(commands.Context)
    ctx.message = mock.Mock(discord.Message)

    with mock.patch("ibis.reply.success") as mock_success:
        # pylint: disable-next=too-many-function-args
        await cog.csvmembers(cog, ctx)
        ctx.typing.assert_called_once_with()
        builder.build_csv.assert_called_once_with(ctx.guild)
        mock_success.assert_called_once_with(ctx, file=builder.build_csv.return_value)


@pytest.mark.asyncio
async def test_command_failure():
    builder = mock.Mock(CsvMembersBuilder)
    builder_cls = mock.Mock(return_value=builder)
    cog = CsvMembersCog(builder_cls=builder_cls)

    ctx = mock.AsyncMock(commands.Context)
    ctx.message = mock.Mock(discord.Message)

    with mock.patch("ibis.reply.fail") as mock_fail:
        builder.build_csv.side_effect = Exception("Test exception")
        with pytest.raises(Exception, match="Test exception"):
            # pylint: disable-next=too-many-function-args
            await cog.csvmembers(cog, ctx)

        ctx.typing.assert_called_once_with()
        builder.build_csv.assert_called_once_with(ctx.guild)
        mock_fail.assert_called_once_with(
            ctx, "Building member CSV failed, please see log."
        )


@pytest.mark.asyncio
async def test_csvmembers_builder():
    builder = CsvMembersBuilder()

    role_admin = mock.Mock(discord.Role)
    role_admin.name = "Admin"

    role_moderator = mock.Mock(discord.Role)
    role_moderator.name = "Moderator"

    role_everyone = mock.Mock(discord.Role)
    role_everyone.name = "@everyone"

    guild = mock.AsyncMock(
        discord.Guild,
        members=[
            mock.Mock(
                discord.Member,
                display_name="First User",
                global_name="First User",
                roles=[role_admin, role_moderator, role_everyone],
            ),
            mock.Mock(
                discord.Member,
                display_name="Second User",
                global_name="Second User Diff Name",
                roles=[role_moderator, role_everyone],
            ),
            mock.Mock(
                discord.Member,
                display_name="Third User",
                global_name="Third User",
                roles=[role_everyone],
            ),
        ],
    )

    guild.members[0].name = "first_user"
    guild.members[1].name = "second_user"
    guild.members[2].name = "third_user"

    csv_file = builder.build_csv(guild)
    assert isinstance(csv_file, discord.File)

    content = csv_file.fp.getvalue().splitlines()
    assert "Username,Guild Display Name,Display Name (If Different),Roles" in content
    assert "first_user,First User,,@Admin @Moderator" in content
    assert "second_user,Second User,Second User Diff Name,@Moderator" in content
    assert "third_user,Third User,," in content
