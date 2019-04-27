import React from 'react';

const STATUS_ENDPOINT = "http://localhost:5000/serverstatus.json";
const START_ENDPOINT = "http://localhost:5000/start_server";

class ServerStatus extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      hasChecked: false,
      serverOnline: false,
      numPlayers: 0,
      serverVersion: null,
      isServerStarting: false,
    };
  }

  componentDidMount() {
    this.checkStatus();
  }

  async checkStatus() {
    const response = await fetch(STATUS_ENDPOINT, {
      method: "GET",
      headers: new Headers({
        "Authorization": "Bearer " + this.props.googleIDToken,
      }),
    });

    if (response.status === 200) {
      const json = await response.json();
      this.setState({
        hasChecked: true,
        serverOnline: json.online,
        numPlayers: json.players,
        serverVersion: json.version,
      });
    } else {
      console.table(response);
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
      alert('Server is started. Please check.');
    } else {
      alert('Server failed to launch');
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
    let status = this.state.serverOnline ? "online" : "offline";
    // Currently checking status
    if (!this.state.hasChecked) {
      return (
        <div>
          Checking server status...
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
        </div>
      );
    }

    // The server is starting
    if (this.state.isServerStarting) {
      return (
        <div>The server is starting. Wait patiently.</div>
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
