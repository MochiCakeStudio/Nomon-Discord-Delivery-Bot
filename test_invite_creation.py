import sqlite3
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

# Add paths to import the cog
sys.path.append('.')
sys.path.append('..')
sys.path.append('cogs')

# Import the cog
with open('../cogs/forum_bump_cog.py', 'r', encoding='utf-8') as f:
    exec(f.read())

class MockBot:
    def __init__(self):
        self.user = MagicMock()
        self.user.id = 123456789

def test_invite_creation_logic():
    """Test the invite creation logic in handle_registration_submit."""
    print("Testing invite creation logic...")

    # Setup mock bot and cog
    bot = MockBot()
    cog = ForumBumpCog(bot)

    # Create test database
    test_db_path = 'test_invite.db'
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

    cog.db_path = test_db_path
    cog.init_db()

    # Insert test server
    conn = cog.get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO servers (server_id, forum_channel_id, server_name) VALUES (?, ?, ?)',
                   (1001, 2001, 'Test Server'))
    conn.commit()
    conn.close()

    # Mock interaction and guild
    mock_interaction = AsyncMock()
    mock_guild = MagicMock()
    mock_guild.id = 1001
    mock_guild.name = 'Test Server'
    mock_interaction.guild = mock_guild
    mock_interaction.followup = AsyncMock()

    # Mock text channels - some allow invites, some don't
    mock_channel1 = MagicMock()
    mock_channel1.permissions_for.return_value.create_instant_invite = False

    mock_channel2 = MagicMock()
    mock_channel2.permissions_for.return_value.create_instant_invite = True
    mock_invite = MagicMock()
    mock_invite.url = 'https://discord.gg/testinvite'
    mock_channel2.create_invite = AsyncMock(return_value=mock_invite)

    mock_guild.text_channels = [mock_channel1, mock_channel2]

    # Mock forum creation and thread creation
    mock_forum = MagicMock()
    mock_forum.available_tags = []
    mock_thread = MagicMock()
    mock_thread.thread = MagicMock()
    mock_thread.thread.id = 3001
    mock_thread.thread.jump_url = 'https://discord.com/channels/1001/3001'
    mock_forum.create_thread = AsyncMock(return_value=mock_thread)

    with patch('discord.utils.find', return_value=None), \
         patch.object(mock_guild, 'create_forum', new_callable=AsyncMock, return_value=mock_forum):

        # Test new registration
        print("Testing new server registration with invite creation...")
        try:
            # Run the method
            asyncio.run(cog.handle_registration_submit(
                mock_interaction,
                'Test Server',
                'Test advertisement',
                'RP, Community',
                edit_mode=False
            ))

            # Check if invite was created on the correct channel
            mock_channel2.create_invite.assert_called_once_with(max_age=0, max_uses=0, embed=False, reason="Permanent invite for Nomon's partner network")

            # Check database for saved invite
            conn = cog.get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT invite_url FROM servers WHERE server_id = ?', (1001,))
            result = cursor.fetchone()
            conn.close()

            if result and result[0] == 'https://discord.gg/testinvite':
                print("✅ Invite URL correctly saved to database")
            else:
                print(f"❌ Invite URL not saved correctly. Got: {result}")

            # Check if followup was sent
            mock_interaction.followup.send.assert_called_once()
            followup_call = mock_interaction.followup.send.call_args[0][0]
            if '🍓 Your partner thread has been created' in followup_call:
                print("✅ Success message sent")
            else:
                print(f"❌ Unexpected followup message: {followup_call}")

        except Exception as e:
            print(f"❌ Error during registration test: {e}")
            import traceback
            traceback.print_exc()

    # Test edit mode
    print("\nTesting edit registration with invite update...")
    try:
        # Insert partner thread for edit mode
        conn = cog.get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO partner_threads (server_id, thread_id) VALUES (?, ?)', (1001, 3001))
        conn.commit()
        conn.close()

        # Mock thread for edit
        mock_existing_thread = AsyncMock()
        mock_existing_thread.name = 'Old Name'
        mock_existing_thread.edit = AsyncMock()
        mock_existing_thread.parent = MagicMock()
        mock_existing_thread.parent.available_tags = []
        mock_existing_thread.history = AsyncMock(return_value=[
            MagicMock(author=MagicMock(id=bot.user.id), edit=AsyncMock())
        ])

        with patch.object(cog.bot, 'fetch_channel', return_value=mock_existing_thread):
            # Run edit
            asyncio.run(cog.handle_registration_submit(
                mock_interaction,
                'Test Server',
                'Updated advertisement',
                'ERP',
                edit_mode=True
            ))

            # Check if invite was created again
            assert mock_channel2.create_invite.call_count == 2  # Called once for new, once for edit

            # Check database updated
            conn = cog.get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT invite_url FROM servers WHERE server_id = ?', (1001,))
            result = cursor.fetchone()
            conn.close()

            if result and result[0] == 'https://discord.gg/testinvite':
                print("✅ Invite URL updated in database during edit")
            else:
                print(f"❌ Invite URL not updated. Got: {result}")

            # Check followup
            followup_calls = mock_interaction.followup.send.call_args_list
            if len(followup_calls) == 2:  # One for new, one for edit
                edit_call = followup_calls[1][0][0]
                if '✨ Your server registration has been updated' in edit_call:
                    print("✅ Edit success message sent")
                else:
                    print(f"❌ Unexpected edit followup: {edit_call}")
            else:
                print(f"❌ Wrong number of followup calls: {len(followup_calls)}")

    except Exception as e:
        print(f"❌ Error during edit test: {e}")
        import traceback
        traceback.print_exc()

    # Cleanup
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

    print("\nInvite creation testing completed.")

if __name__ == "__main__":
    import asyncio
    test_invite_creation_logic()
