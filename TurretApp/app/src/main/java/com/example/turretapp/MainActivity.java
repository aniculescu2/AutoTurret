package com.example.turretapp;

import static android.view.MotionEvent.ACTION_DOWN;
import static android.view.MotionEvent.ACTION_UP;

import android.os.Bundle;
import android.util.Log;
import android.view.MotionEvent;
import android.view.View;
import android.widget.Switch;
import android.widget.TextView;

import androidx.activity.EdgeToEdge;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.graphics.Insets;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowInsetsCompat;

import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.ProtocolException;
import java.net.URL;

public class MainActivity extends AppCompatActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        EdgeToEdge.enable(this);
        setContentView(R.layout.activity_main);
        ViewCompat.setOnApplyWindowInsetsListener(findViewById(R.id.main), (v, insets) -> {
            Insets systemBars = insets.getInsets(WindowInsetsCompat.Type.systemBars());
            v.setPadding(systemBars.left, systemBars.top, systemBars.right, systemBars.bottom);
            return insets;
        });
        findViewById(R.id.rotateLeft).setOnTouchListener(holdToTurret);
        findViewById(R.id.rotateRight).setOnTouchListener(holdToTurret);
        findViewById(R.id.fire).setOnTouchListener(holdToTurret);
        findViewById(R.id.power).setOnClickListener(connectToTurret);
    }

    private final View.OnClickListener connectToTurret = new View.OnClickListener(){
        @Override
        public void onClick(View v) {
            int action = 0;
            if (v.getId() == R.id.rotateLeft)
                action = 1;
            else if (v.getId() == R.id.rotateRight)
                action = 2;
            else if (v.getId() == R.id.fire)
                action = 3;
            else if (v.getId() == R.id.power)
                action = 4;
            HTTPThread thread = new HTTPThread(action);
            thread.start();
        }
    };

    MotionEvent leftState, rightState, fireState;

    private final View.OnTouchListener holdToTurret = new View.OnTouchListener(){

        @Override
        public boolean onTouch(View v, MotionEvent event){
            int action = 0;
            if (v.getId() == R.id.rotateLeft) {
                action = 1;
                leftState = event;
            }
            else if (v.getId() == R.id.rotateRight) {
                action = 2;
                rightState = event;
            }
            else if (v.getId() == R.id.fire) {
                action = 3;
                fireState = event;
            }
            if (event.getActionMasked() == ACTION_DOWN || event.getActionMasked() == ACTION_UP){
                HTTPThread thread = new HTTPThread(action);
                thread.start();
            }
            return false;
        }
    };

    private
    class HTTPThread extends Thread {
        int action;
        String url = "http://172.28.131.111:8080/";
        HttpURLConnection urlConnection;

        HTTPThread(int action) {
            this.action = action;
        }

        public void run() {
            try {
                URL url = new URL(this.url);

                urlConnection = (HttpURLConnection) url.openConnection();
                urlConnection.setDoOutput(true);
                urlConnection.setRequestMethod("POST");
                urlConnection.setRequestProperty("Content-Type", "text/plain");
                urlConnection.setRequestProperty("charset", "utf-8");
            }
            catch (ProtocolException e) {
                System.out.println("protocol exception");
            }
            catch (IOException e){
                System.out.println("Io exception in connection");
            }
            String input = "";
            switch(action) {
                case 1:
                    if (leftState.getActionMasked() == ACTION_DOWN) {
                        input = "start left\0";
                    }
                    else{
                        input = "stop left\0";
                    }
                    break;
                case 2:
                    if (rightState.getActionMasked() == ACTION_DOWN) {
                        input = "start right\0";
                    }
                    else{
                        input = "stop right\0";
                    }
                    break;
                case 3:
                    if (fireState.getActionMasked() == ACTION_DOWN) {
                        input = "start fire\0";
                    }
                    else{
                        input = "stop fire\0";
                    }
                    break;
                case 4:
                    Switch powerSwitch = findViewById(R.id.power);
                    input = powerSwitch.isChecked() ? "auto\0" : "manual\0";
                    break;
            }
            if (action <= 4) {
                try {
                    OutputStream out = new BufferedOutputStream(urlConnection.getOutputStream());
                    out.write(input.getBytes());
                    out.flush();

                    InputStream in = new BufferedInputStream(urlConnection.getInputStream());
                    String TAG = MainActivity.class.getSimpleName();
                    String message = convertStreamToString(in);
                    Log.e(TAG, ">>>>>PRINTING<<<<<");
                    Log.e(TAG, message);

                    runOnUiThread(new Runnable() {
                        @Override
                        public void run() {
                            TextView messages = findViewById(R.id.messages);
                            messages.setText(message);
                        }
                    });
                } catch (IOException e) {
                    System.out.println("IO exception");
                    e.printStackTrace(System.out);
                } finally {
                    urlConnection.disconnect();
                }
            }
        }
    }
    String convertStreamToString(java.io.InputStream is) {
        try {
            return new java.util.Scanner(is).useDelimiter("\\A").next();
        } catch (java.util.NoSuchElementException e) {
            return "No such element exception";
        }
    }
}