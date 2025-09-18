# 🎬 Overseerr Telegram Bot
The **Overseerr Telegram Bot** enables seamless interaction with your Overseerr instance through Telegram. Search for movies and TV shows, check availability, request new titles, report issues, and manage notifications—all from your Telegram chat. With flexible operation modes, admin controls, and optional password protection, the bot is designed for both individual and group use, making media management effortless.

*Seamlessly manage your media server through Telegram*📚 **Detailed Documentation**: Explore the [Wiki](https://github.com/hasan-sayfi/OverseerrRequestViaTelegramBot/wiki) for comprehensive guides on setup, configuration, and advanced usage.



[![Version](https://img.shields.io/badge/version-4.2.1-blue.svg)](./CHANGELOG.md)

[![Docker Pulls](https://img.shields.io/docker/pulls/hsayfi/overseerr-telegram-bot)](https://hub.docker.com/r/hsayfi/overseerr-telegram-bot)

[![License](https://img.shields.io/badge/license-GPL--3.0-green.svg)](./LICENSE)

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)

[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](./DOCKER.md)


## Features



**Transform your media management experience with intelligent Telegram integration for Overseerr**- **Media Search**: Use `/check <title>` to find movies or TV shows (e.g., `/check The Matrix`) and view detailed results, including posters and availability.

- **Availability Check**: Instantly see if a title is available in HD (1080p) or 4K, based on your Overseerr library.


- **Title Requests**: Request missing titles in HD, 4K, or both, respecting Overseerr user permissions for quality settings.

- **Issue Reporting**: Report issues like video glitches, audio sync problems, missing subtitles, or other playback errors for existing titles.

- **Notification Management**: Customize Telegram notifications for Overseerr events (e.g., request approvals, media availability) with options to enable/disable or use silent mode.

- **Admin Controls**: Admins can switch operation modes, toggle Group Mode, create new Overseerr users, and manage bot settings via an intuitive menu.

---- **Password Protection**: Secure bot access with an optional password, ensuring only authorized users can interact.

- **Group Mode**: Restrict bot usage to a specific Telegram group or thread, ideal for collaborative media management in shared environments like family or friend groups.

## ✨ What's New in v4.2.1

> [!Note]

🔐 **Admin Request Approval System** - Complete moderation workflow with real-time notifications  > The language of media titles and descriptions matches the language setting configured in Overseerr (e.g., German titles and descriptions if Overseerr is set to German), while the bot's interface remains in English.

🐳 **Enhanced Docker Support** - Updated to Python 3.13 for improved security and performance  

📊 **Advanced Request Management** - Intelligent retry logic and comprehensive error handling  ![1 Start](https://github.com/user-attachments/assets/55cc4796-7a4f-4909-a260-0395e7fb202a)

🧪 **Comprehensive Testing** - 650+ lines of automated tests for reliability  



------



## 🎯 Features## Installation



### Core FunctionalityFor detailed installation instructions, refer to the [Wiki](https://github.com/LetsGoDude/OverseerrRequestViaTelegramBot/wiki#installation):

- **🔍 Smart Media Search** - Find movies and TV shows with fuzzy matching and detailed results

- **📊 Real-time Availability** - Check HD (1080p) and 4K availability across your media library- **Ubuntu (Source Installation)**: Follow the guide at [Installation on Ubuntu](https://github.com/LetsGoDude/OverseerrRequestViaTelegramBot/wiki#source-installation-ubuntulinux).

- **🎬 One-click Requests** - Request missing titles with quality preferences- **Docker**: Deploy with [Docker](https://github.com/LetsGoDude/OverseerrRequestViaTelegramBot/wiki#docker-installation-without-compose), [Docker Compose](https://github.com/LetsGoDude/OverseerrRequestViaTelegramBot/wiki#docker-installation-with-compose) or [NAS Container](https://github.com/LetsGoDude/OverseerrRequestViaTelegramBot/wiki#nas-container-setup) using the instructions at the wiki.

- **🐛 Issue Reporting** - Report video, audio, subtitle, and playback problems

- **🔔 Smart Notifications** - Customizable Telegram alerts for media events---



### Advanced Features## Operation Modes

- **🔐 Admin Approval System** - Complete request moderation with interactive controls

- **👥 Multi-user Support** - Flexible operation modes for different scenariosThe bot supports three operation modes, configurable by the admin via `/settings`, catering to different use cases:

- **🔒 Security First** - Optional password protection and role-based access

- **🏢 Group Mode** - Collaborative media management for teams and families- **Normal Mode**:

- **🌍 Multi-language** - Respects Overseerr language settings

  - Users log in with their individual Overseerr credentials (email and password).

> [!Note]  - Requests and issue reports are tied to each user’s Overseerr account, ensuring personalized tracking.

> Media titles and descriptions match your Overseerr language settings, while the bot interface remains in English.  - Ideal for users with their own Overseerr accounts who want full control over their requests and notifications.



![1 Start](https://github.com/user-attachments/assets/55cc4796-7a4f-4909-a260-0395e7fb202a)- **API Mode**:



---  - Users select an existing Overseerr user from a list without needing credentials, using the Overseerr API key for requests.

  - Simplifies access for users without Overseerr accounts, with requests automatically approved by Overseerr.

## 🚀 Quick Start  - Issue reports are attributed to the admin’s account due to API key usage.

  - Best for environments where quick access is prioritized over individual account management.

### Docker (Recommended)

- **Shared Mode**:

```bash

# Pull and run with Docker  - All users share a single Overseerr account configured by the admin, streamlining group usage.

docker run -d \  - The admin logs in once, and all requests and issue reports use this shared account.

  --name overseerr-telegram-bot \  - Perfect for small groups (e.g., families or friends) sharing a media server, with notifications sent to a common Telegram chat.

  -e TELEGRAM_TOKEN="your_bot_token" \

  -e OVERSEERR_API_URL="http://your-overseerr:5055/api/v1" \Learn more about configuring modes in the [Wiki](https://github.com/LetsGoDude/OverseerrRequestViaTelegramBot/wiki#operation-modes).

  -e OVERSEERR_API_KEY="your_api_key" \

  chimpanzeesweetrolls/overseerrrequestviatelegrambot:latest---



# Or use Docker Compose (recommended for production)### User Commands

curl -O https://raw.githubusercontent.com/hasan-sayfi/OverseerrRequestViaTelegramBot/main/docker/docker-compose.yml

docker-compose up -d

```- **/start**:



### Python Installation  - Initializes the bot, displaying a welcome message with the bot’s version and prompting for a password (if enabled).

  - The first user to run `/start` becomes an admin if no admins exist.

```bash  - In Group Mode, sets the current chat/thread as the primary chat for bot interactions.

# Clone and install  - Guides users to log in (Normal Mode), select a user (API Mode), or rely on the shared account (Shared Mode).

git clone https://github.com/hasan-sayfi/OverseerrRequestViaTelegramBot.git  - Example: `/start`

cd OverseerrRequestViaTelegramBot

pip install -r requirements.txt

- **/check <title>**:

# Configure environment

cp .env.template .env  - Searches Overseerr for movies or TV shows and returns a paginated list with detailed results (e.g., title, availability, request status).

# Edit .env with your credentials  - Displays availability status (e.g., 1080p available, 4K requestable) and options to request missing formats or report issues for existing media.

  - Supports Overseerr’s language settings for titles and descriptions.

# Run the bot  - Example: `/check Breaking Bad`

python bot.py

```

- **/settings**:

📚 **Detailed Setup**: Visit our [Wiki](https://github.com/LetsGoDude/OverseerrRequestViaTelegramBot/wiki) for comprehensive installation guides.

  - Opens an interactive menu to manage Overseerr accounts and bot settings.

---  - **For Users**:

    - Normal Mode: Log in with Overseerr credentials (email/password) or log out.

## 🎛️ Operation Modes    - API Mode: Select an Overseerr user from a list.

    - Shared Mode: Limited to viewing the shared account status (set by the admin).

Choose the mode that best fits your setup:    - Manage notifications (enable/disable, silent mode) after selecting an Overseerr user.

  - Example: `/settings`

| Mode | Use Case | Authentication | Best For |

|------|----------|----------------|----------|

| **🔐 Normal** | Individual accounts | Personal Overseerr credentials | Multi-user environments |### Admin Commands

| **🔑 API** | Simplified access | Select from user list | Quick access without credentials |

| **👥 Shared** | Group usage | Single shared account | Families, small teams |All admin actions are performed via the `/settings` menu:



Configure modes through the admin settings menu accessible via `/settings`.
- **Change Operation Mode**: Switch between Normal, API, and Shared modes to adjust bot behavior.

- **Toggle Group Mode**: Enable/disable Group Mode and set the primary chat/thread for bot interactions.

- **User Management**:

  - Authorize or block users to control bot access.

## 💬 Commands  - Promote users to admin or demote them.

  - Create new Overseerr users by providing an email and username.

### User Commands  - View and manage all users in a paginated list.

- **`/start`** - Initialize bot, set up authentication, become admin (first user)- **Login/Logout (Shared Mode)**: Admins manage the shared Overseerr account login.

- **`/check <title>`** - Search for movies/TV shows (e.g., `/check Breaking Bad`)

- **`/settings`** - Manage account, notifications, and preferences
![2 settings](https://github.com/user-attachments/assets/7ecd389c-e931-42a4-bcec-c5c45fe4029b)
![3 settings - User Management](https://github.com/user-attachments/assets/95c6d9fd-eb3d-44ed-8b5a-eb7e43c1eb22)

### Admin Controls

Access via `/settings` menu:---

- **Operation Mode Management** - Switch between Normal/API/Shared modes

- **Group Mode Toggle** - Enable collaborative group usage## Managing Notifications

- **User Management** - Authorize, block, promote users

- **Request Approval** - Moderate user requests with real-time notificationsUsers can configure Overseerr Telegram notifications via `/settings`:

- **Overseerr Integration** - Create new users, manage shared accounts

- **Enable/Disable Notifications**: Turn on/off notifications for events like request approvals, media availability, or errors.
![2 settings](https://github.com/user-attachments/assets/7ecd389c-e931-42a4-bcec-c5c45fe4029b)

- **Silent Mode**: Opt for silent notifications without sound, ideal for minimizing disruptions during quiet hours.
![3 settings - User Management](https://github.com/user-attachments/assets/95c6d9fd-eb3d-44ed-8b5a-eb7e43c1eb22)
- In Shared Mode, only admins configure notifications for the shared account, applying to all users.


* Example: Enable notifications to receive a Telegram message when "The Witcher" becomes available, or set silent mode for nighttime updates.



## 🔔 Notification Management---



Customize your notification experience:## Reporting Issues

- **Smart Alerts** - Request approvals, media availability, system events

- **Silent Mode** - Notifications without sound for quiet hoursFrom media details returned by `/check`, users can report issues for pending or available titles, such as:

- **Granular Control** - Enable/disable specific notification types

- **Group Notifications** - Shared alerts in collaborative environments- Video issues (e.g., pixelation, buffering)

- Audio issues (e.g., out-of-sync, missing tracks)

---- Subtitle issues (e.g., incorrect timing, missing files)

- Other playback problems

## 🐛 Issue Reporting

Reports are submitted to Overseerr, with attribution based on the operation mode (individual user in Normal Mode, admin in API Mode, shared account in Shared Mode).

Report media problems directly from search results:
- **Video Issues**: Pixelation, buffering, quality problems.

![4 Check - Status der anforderung und problem melden](https://github.com/user-attachments/assets/4dd828ed-df99-4861-bff9-b40c758c0b24)

- **Audio Issues**: Sync problems, missing tracks, quality issues

![7 Problem](https://github.com/user-attachments/assets/8cb1322e-4b32-4b44-8873-65f6a9e6b471)

- **Subtitle Issues** - Timing problems, missing files, encoding issues

- **General Playback** - Any other streaming or playback problems---



![4 Check - Status der anforderung und problem melden](https://github.com/user-attachments/assets/4dd828ed-df99-4861-bff9-b40c758c0b24)## Group Mode
![7 Problem](https://github.com/user-attachments/assets/8cb1322e-4b32-4b44-8873-65f6a9e6b471)

Group Mode enhances collaborative usage by restricting bot interactions to a designated Telegram group or thread:

---

- **Enable Group Mode**: Only the admin can activate this via `/settings`, storing the setting in `data/bot_config.json`.

## 👥 Group Mode- **Set Primary Chat**: Running `/start` in a group or thread sets it as the primary chat, identified by `primary_chat_id`.

- **Usage**: When active, all commands (`/start`, `/check`) and notifications are confined to the primary chat/thread, ignoring other chats. This ensures a unified experience for group members.

Perfect for collaborative media management:- **Example**: In a family Telegram group, users request "Toy Story" via `/check`, and the bot responds only in that group, with notifications (e.g., “Toy Story is available”) sent to all members.

- **Centralized Communication** - All interactions in designated group/thread- **Use Case**: Ideal for shared media servers (e.g., Plex) where a group collaborates on requests, keeping communication centralized.

- **Shared Requests** - Team members collaborate on media requests

- **Unified Notifications** - Everyone stays informed about media availabilityFor setup details, visit the [Wiki](https://github.com/LetsGoDude/OverseerrRequestViaTelegramBot/wiki#group-mode).

- **Access Control** - Admin controls who can participate

---

**Setup**: Enable via admin `/settings`, then run `/start` in your target group.

## FAQ and Troubleshooting

---

- **How do I set up the bot for the first time?**\

## 📁 Project Structure  Follow the installation guides in the [Wiki](https://github.com/LetsGoDude/OverseerrRequestViaTelegramBot/wiki) for Ubuntu or Docker.



| Folder | Purpose |- **What if I forget the bot password?**\

|--------|---------|  The password is set via the `PASSWORD` environment variable or `config.py`. Admins can reset it by updating the configuration. See the [Wiki](https://github.com/LetsGoDude/OverseerrRequestViaTelegramBot/wiki) for details.

| `api/` | Overseerr API integration and request management |

| `handlers/` | Telegram command and callback handlers |- **Why can’t I request 4K titles?**  

| `notifications/` | Webhook system and notification management |  4K requests depend on Overseerr permissions:

| `config/` | Configuration management and constants |  - Normal Mode: Tied to the user’s account permissions.

| `session/` | User session and authentication handling |  - API Mode: Tied to the selected user’s permissions.

| `docker/` | Docker deployment files and configurations |  - Shared Mode: Tied to the shared account’s permissions.  

| `docs/` | Comprehensive project documentation |  Check Overseerr settings or contact your admin.

| `tests/` | Automated testing suite |

| `utils/` | Utility functions and error handling |- **Why don’t I see the “Manage Notifications” option in /settings?**  

  The “Manage Notifications” button appears only after selecting an Overseerr user (via login in Normal Mode, user selection in API Mode, or admin login in Shared Mode). Use `/settings` to log in or select a user first.

---

- **How do I troubleshoot bot errors?**  

## 🆘 FAQ & Troubleshooting  Check the bot logs in the console or `data/` directory. Common issues include incorrect `TELEGRAM_TOKEN`, `OVERSEERR_API_URL`, or `OVERSEERR_API_KEY`. Refer to the [Wiki](https://github.com/LetsGoDude/OverseerrRequestViaTelegramBot/wiki) for troubleshooting tips.



<details>---

<summary><strong>🔧 First-time setup help</strong></summary>

## Contributing

Follow our comprehensive [Wiki installation guides](https://github.com/LetsGoDude/OverseerrRequestViaTelegramBot/wiki) for Ubuntu or Docker deployment.

</details>Contributions are welcome!



<details>---

<summary><strong>🔑 Forgot bot password?</strong></summary>

## License

Update the `PASSWORD` environment variable or edit `config.py`. See the [Wiki](https://github.com/LetsGoDude/OverseerrRequestViaTelegramBot/wiki) for details.

</details>This project is licensed under the GPL-3.0 License. See the [LICENSE](https://github.com/LetsGoDude/OverseerrRequestViaTelegramBot/blob/main/LICENSE) file for details.



<details>---

<summary><strong>🎬 Can't request 4K titles?</strong></summary>

## Contact

4K availability depends on your Overseerr account permissions. Check your Overseerr user settings or contact your admin.

</details>For issues or feature requests, open an issue on [GitHub](https://github.com/LetsGoDude/OverseerrRequestViaTelegramBot/issues).



<details>---

<summary><strong>🔔 Missing notification options?</strong></summary>

Built with :heart: for media enthusiasts!

The notification menu appears after selecting an Overseerr user. Use `/settings` to log in or select a user first.
</details>

<details>
<summary><strong>🐛 Bot errors or issues?</strong></summary>

Check bot logs for common issues like incorrect `TELEGRAM_TOKEN`, `OVERSEERR_API_URL`, or `OVERSEERR_API_KEY`. Visit our [troubleshooting guide](https://github.com/LetsGoDude/OverseerrRequestViaTelegramBot/wiki) for detailed help.
</details>

---

## 🚀 Recent Enhancements

### v4.2.x Series
- **🔐 Complete Admin Approval System** with interactive moderation
- **🐳 Docker Infrastructure Upgrade** to Python 3.13
- **📊 Enhanced API Integration** with intelligent retry logic
- **🧪 Comprehensive Test Coverage** for reliability assurance
- **🛠️ Advanced Error Handling** and logging capabilities

See the full [CHANGELOG.md](./CHANGELOG.md) for detailed version history.

---

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. **🐛 Report Issues** - Found a bug? [Open an issue](https://github.com/hasan-sayfi/OverseerrRequestViaTelegramBot/issues)
2. **💡 Suggest Features** - Have an idea? We'd love to hear it!
3. **🔧 Submit PRs** - Fix bugs or add features through pull requests
4. **📚 Improve Docs** - Help make our documentation even better
5. **⭐ Star the Repo** - Show your support and help others discover the project

---

## 📜 License

This project is licensed under the **GPL-3.0 License** - see the [LICENSE](./LICENSE) file for details.

---

## 📞 Support & Community

- **🐛 Issues & Bugs**: [GitHub Issues](https://github.com/hasan-sayfi/OverseerrRequestViaTelegramBot/issues)
- **💬 Discussions**: [GitHub Discussions](https://github.com/hasan-sayfi/OverseerrRequestViaTelegramBot/discussions)
- **📚 Documentation**: [Project Wiki](https://github.com/hasan-sayfi/OverseerrRequestViaTelegramBot/wiki)
- **🐳 Docker Images**: [Docker Hub](https://hub.docker.com/r/hsayfi/overseerr-telegram-bot)

---

## ❤️ Big Thanks
- **Original Source**: [GitHub Project](https://github.com/hasan-sayfi/OverseerrRequestViaTelegramBot/issues)
- **Originally Forked**: [GitHub Project](https://github.com/solangegamboa/OverseerrRequestViaTelegramBot)
---


<div align="center">

**Built with ❤️ for media enthusiasts worldwide**

*Transform your media server experience today!*

</div>