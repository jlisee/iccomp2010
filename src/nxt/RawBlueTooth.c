
/*****************************************************************************/
/*                                T Y P E S                                  */
/*****************************************************************************/

static const int MAX_ROBOTS = 10;
static const int MAX_BALLS = 256;

/*****************************************************************************/
/*                                T Y P E S                                  */
/*****************************************************************************/

typedef struct
{
  float x;
  float y;
} Vector2D;

typedef struct
{
  ubyte id;
  float heading;
  Vector2D pos;
} RobotInfo;

typedef struct
{
  // TODO: send both robot poses?
  ubyte numRobots;
  ubyte numBalls;
} PosInfoHeader;

typedef ubyte ReadBytesBuffer[256];
typedef RobotInfo RobotInfoList[MAX_ROBOTS];
typedef Vector2D BallPositionList[MAX_BALLS];

/*****************************************************************************/
/*                              G L O B A L S                                */
/*****************************************************************************/

/** Buffer for reading from serial port */
ReadBytesBuffer g_btReadBuffer;

/** Header for the robot and ball counts */
PosInfoHeader g_posInfoHeader;

/** All current balls on the field (g_posInfoHeader has total count) */
BallPositionList g_allBallPositions;

/*****************************************************************************/
/*                                 M A T H                                   */
/*****************************************************************************/

// TODO:
// Vector2D: init, add, subtract, dot, length (squareLength?), normalize

float atan2(float y, float x)
{
  float phi;   //phi=radians;

  if (x>0) {
    phi=atan(y/x);
  } else if ((x<0)&&(y>=0)) {
    phi=PI+atan(y/x);
  } else if ((x<0)&&(y<0)){
    phi=-PI+atan(y/x);
  } else if ((x==0)&&(y>0)) {
    phi=PI/2;
  } else if ((x==0)&&(y<0)) {
    phi=-PI/2;
  } else if ((x==0)&&(y==0)) {
    phi=0;
  }

  return phi;
}


/*****************************************************************************/
/*                          B L U E T O O T H  I O                           */
/*****************************************************************************/

/** Checks for connected bluetooth status and reports negative results */
void BTcheckLinkConnected()
{
  if (nBTCurrentStreamIndex >= 0)
    return;  // An existing Bluetooth connection is present.

  //
  // Not connected. Audible notification and LCD error display
  //
  PlaySound(soundLowBuzz);
  PlaySound(soundLowBuzz);
//  eraseDisplay();
  nxtDisplayCenteredTextLine(3, "Computer Not");
  nxtDisplayCenteredTextLine(4, "Connected");
  wait1Msec(3000);
  StopAllTasks();
}

/** Enables raw Bluetooth mode so that we can talk directly over the serial port */
void BTenableRawMode()
{
  // Set Bluetooth to "raw mode".
  setBluetoothRawDataMode();
  wait1Msec(50);

  // While the Bluecore is still NOT in raw mode (bBTRawMode == false);
  while (!bBTRawMode)
  {
    // Wait for Bluecore to enter raw data mode.
    wait1Msec(5);
  }
}

/** Reads the desired number of bytes from the raw bluetooth feed */
void BTreadBytes(ReadBytesBuffer& buffer, int bytesToRead)
{
  //int bytesRead = 0;
  ubyte localBuf[1];

  //while (bytesRead < bytesToRead)
  for (int i = 0; i < bytesToRead; ++i)
  {
    while (0 == nxtReadRawBluetooth(localBuf, 1))
    {
      // Do nothing right now, but spin for right now
    }

    // Store value in the given buffe
    buffer[i] = localBuf[0];

    // Increment the number of bytes read
    //bytesRead += 1;
  }
}




/*****************************************************************************/
/*                 C O M M S   P R O T O C O L  E N G I N E                  */
/*****************************************************************************/

/** Syncs up with the incoming position info message stream */
void COMsync()
{
  // Read in a byte at a time keeping track of the last two bytes
  // When both bytes are 255 we are synced
}

void COMParseFloat(ubyte data, float& num)
{

}

void COMParseVector2D(Vector2D& vec)
{
  // Read in two bytes
  // Convert to floats
}

void COMReadRobotInfo(Vector

void COMreadHeader(PosInfoHeader& header, int justSynced)
{
  // If not justSynced read in the two sync bytes

  // Read in first pos

  // Read in second pos

  // Read in num balls
}

void COMreadBalls(int numBalls, BallPositionList& ballList)
{
  // Reads in all the balls (3 byte packets each)
}

// TODO:
// comms task
//  - does all BT initialization
//  - runs sync on startup
//  - read headers/balls in an infinte loop (with a proper wait time)

void COMupdate()
{
}

void COMstart()
{
}

void COMstop()
{
}

/*****************************************************************************/


// Main
task main()
{
  /// IDEA: Use left/right button press to designate robot starting position
  ///       even have a handshake when the robot first boots up

  // NXT will play 'alert' tone when Bluetooth is automatically connected or
  // disconnects
  bBTHasProgressSounds = true;

  // NXT will always use default password. Will not prompt for manual password
  // entry
  bBTSkipPswdPrompt = true;

  // Test whether NXT is visible (i.e responds) to other BT devices during a
  // search
  if (!bBTVisble)
	{
	  // TODO: make a sad noise and quit probably
	}

	g_allBallPositions[0].x = 5.2;

	// Display the text on line number 1 of 8 on the LCD
	nxtDisplayTextLine(1, "   Hello World  ");
	BTcheckLinkConnected();
	BTenableRawMode();
	nxtDisplayTextLine(2, "Bluetooth Enabled");

	ubyte BytesToSend[5];
	BytesToSend[0] = 'H';
	BytesToSend[1] = 'e';
	BytesToSend[2] = 'l';
	BytesToSend[3] = 'l';
	BytesToSend[4] = 'o';
	nxtWriteRawBluetooth(BytesToSend, 5);
	nxtDisplayTextLine(3, "Message sent");

	// Read in message
	//READ_BYTES_BUFFER bufferBytes;
	ubyte bufferBytes[100];
	for (int i = 0; i < 100; ++i)
	  bufferBytes[i] = 0;


	BTreadBytes((ReadBytesBuffer)bufferBytes, 12);
	//while (0 == nxtReadRawBluetooth(bufferBytes,2))
	//{}

	// Write it to screen
	string input = "";
	StringFromChars(input, bufferBytes);
	string output = "";
	StringFormat(output, "'%s'", input);
	nxtDisplayTextLine(4, output);


	nxtDisplayTextLine(5, "Done");
	wait1Msec(5000);														// Wait a bit otherwise program will finish and text not visible
}
