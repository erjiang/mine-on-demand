import React from 'react';
import Loader from './Loader';

const STATUS_ENDPOINT = "serverstatus.json";
const START_ENDPOINT = "start_server";

class ServerStatus extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      hasChecked: false,
      serverOnline: true,
      numPlayers: 0,
      serverVersion: null,
      isServerStarting: false,
    };
  }

  componentDidMount() {
    ///this.checkStatus();
  }

  async checkStatus() {
    const response = await fetch(STATUS_ENDPOINT, {
      method: "GET",
      headers: new Headers({
        "Authorization": "Bearer " + this.props.googleIDToken,
      }),
    });

    if (response.status === 200) {
      try {
        const json = await response.json();
        this.setState({
          hasChecked: true,
          serverOnline: json.online,
          numPlayers: json.players,
          serverVersion: json.version,
        });
      } catch (e) {
        this.props.onError("Unable to check the status of the server: " + e.message);
        return;
      }
    } else {
      console.table(response);
      this.props.onError("Received a non-200 response. See console.");
    }
  }

  async startServer() {
    this.setState({ isServerStarting: true });

    const response = await fetch(START_ENDPOINT, {
      method: "POST",
      headers: new Headers({
        "Authorization": "Bearer " + this.props.googleIDToken,
      }),
    });

    this.setState({ isServerStarting: false });

    if (response.status === 200) {
      // TODO: This isn't quite right
      setTimeout(() => {
        console.log("The server thinks the server has started.");
        this.setState({
          hasChecked: false,
        });
        this.checkStatus();
      }, 5000);
    } else if (response.status === 409) {
      // The server was already running
      console.log("Received 409: Server was already running.");
      setTimeout(() => {
        this.setState({
          hasChecked: false,
        });
        this.checkStatus();
      }, 5000);
    } else {
      this.props.onError("Unfortunately, the server failed to launch: " + response.body);
      console.table(response);
    }
  }

  onRefreshButtonClick() {
    this.checkStatus();
  }

  onStartServerClick() {
    this.startServer();
  }

  render() {
    // Currently checking status
    if (!this.state.hasChecked) {
      return (
        <div>
          <p>Checking server status.</p>
          <Loader />
        </div>
      );
    }

    // Refresh button
    const refreshButton = <button onClick={() => this.onRefreshButtonClick()}>Refresh</button>;

    // The server is online
    if (this.state.serverOnline) {
      return (
        <div>
          There are {this.state.numPlayers} players online and
          the version is {this.state.serverVersion}.
          <div className="buttonBar">{refreshButton}</div>
          <div className="serverConnectionInfo">
            To connect to this server, use <strong>minecraft.ericjiang.com</strong> as the host name.
            Can't connect? Make sure you are <a href="https://ipv6test.google.com/" rel="noopener noreferrer" target="_blank">on the IPv6 Internet</a>.
          </div>
        </div>
      );
    }

    // The server is starting
    if (this.state.isServerStarting) {
      return (
        <div>
          <p>The server is starting. Wait patiently.</p>
          <Loader />
        </div>
      );
    }

    // The server is offline
    return (
      <div>
        <div>The server is offline.</div>
        <div className="buttonBar">
        <button onClick={() => this.onStartServerClick()}>Start Server</button>
          {refreshButton}
        </div>
      </div>
    );
  }
}

export default ServerStatus;
